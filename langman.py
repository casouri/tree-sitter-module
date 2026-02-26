#!/usr/bin/env python3
"""Tree-sitter grammar builder and installer."""

# --- Imports (stdlib only) ---
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# --- Constants ---
SCRIPT_DIR = Path(__file__).parent.resolve()
CACHE_DIR = SCRIPT_DIR / ".cache"
DIST_DIR = SCRIPT_DIR / "dist"
DEFAULT_INSTALL_DIR = Path.home() / ".emacs.d" / "tree-sitter"

# --- Platform Detection ---
def detect_extension() -> str:
    """Detect the shared library extension for the current platform."""
    system = platform.system()
    if system == "Darwin":
        return "dylib"
    elif system == "Windows":
        return "dll"
    else:
        return "so"


def detect_xattr_method() -> str:
    """Detect the extended attribute method: 'macos', 'linux', or 'fallback'."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif shutil.which("setfattr") and shutil.which("getfattr"):
        return "linux"
    else:
        return "fallback"


# --- Version Attributes ---
def set_version(path: Path, version: str) -> None:
    """Set the version attribute on a file."""
    method = detect_xattr_method()
    if method == "macos":
        subprocess.run(
            ["xattr", "-w", "user.version", version, str(path)],
            check=True,
        )
    elif method == "linux":
        subprocess.run(
            ["setfattr", "-n", "user.version", "-v", version, str(path)],
            check=True,
        )
    else:
        # Fallback: use .version file
        version_file = path.parent / f"{path.name}.version"
        version_file.write_text(version)


def get_version(path: Path) -> Optional[str]:
    """Get the version attribute from a file. Returns None if not set."""
    method = detect_xattr_method()
    try:
        if method == "macos":
            result = subprocess.run(
                ["xattr", "-p", "user.version", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        elif method == "linux":
            result = subprocess.run(
                ["getfattr", "-n", "user.version", "--only-values", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        else:
            # Fallback: use .version file
            version_file = path.parent / f"{path.name}.version"
            if version_file.exists():
                return version_file.read_text().strip()
            return None
    except Exception:
        return None


def has_version(path: Path) -> bool:
    """Check if a file has a version attribute set."""
    return get_version(path) is not None


def load_languages() -> list[str]:
    """Load the list of supported languages from batch.sh."""
    result = subprocess.run(
        [str(SCRIPT_DIR / "batch.sh"), "--list"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [lang.strip() for lang in result.stdout.splitlines() if lang.strip()]


# --- Artifact Naming ---
def artifact_name(lang: str) -> str:
    """Get the artifact filename for a language."""
    ext = detect_extension()
    return f"libtree-sitter-{lang}.{ext}"


# --- Cache ---
def cache_path(lang: str, version: str) -> Path:
    """Get the cache path for a language version."""
    return CACHE_DIR / lang / version


def is_cached(lang: str, version: str) -> bool:
    """Check if a versioned build is cached."""
    cached_artifact = cache_path(lang, version) / artifact_name(lang)
    return cached_artifact.exists() and has_version(cached_artifact)


def get_from_cache(lang: str, version: str, dest: Path) -> Optional[Path]:
    """
    Copy a cached artifact to the destination directory.
    Returns the destination path if successful, None otherwise.
    """
    if not is_cached(lang, version):
        return None

    cached_artifact = cache_path(lang, version) / artifact_name(lang)
    dest.mkdir(parents=True, exist_ok=True)
    dest_artifact = dest / artifact_name(lang)
    shutil.copy2(cached_artifact, dest_artifact)

    # Copy version attribute
    cached_version = get_version(cached_artifact)
    if cached_version:
        set_version(dest_artifact, cached_version)

    return dest_artifact


def add_to_cache(lang: str, version: str, artifact: Path) -> None:
    """Add an artifact to the cache."""
    cache_dir = cache_path(lang, version)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_artifact = cache_dir / artifact.name
    shutil.copy2(artifact, cached_artifact)

    # Copy version attribute
    artifact_version = get_version(artifact)
    if artifact_version:
        set_version(cached_artifact, artifact_version)


# --- Build ---
def build_single(lang: str, version: Optional[str] = None) -> Path:
    """
    Build a single language grammar by calling build.sh.
    Returns the path to the built artifact in dist/.
    """
    art_name = artifact_name(lang)

    # Check cache if version specified
    if version and is_cached(lang, version):
        print(f"Using cached {lang} {version}")
        result = get_from_cache(lang, version, DIST_DIR)
        if result:
            return result

    # Build using build.sh
    cmd = [str(SCRIPT_DIR / "build.sh"), lang]
    if version:
        cmd = [str(SCRIPT_DIR / "build.sh"), "--version", version, lang]

    env = {**os.environ, "INSTALL_DIR": str(DIST_DIR)}
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)

    # Print build output (excluding VERSION line)
    for line in result.stdout.splitlines():
        if not line.startswith("VERSION:"):
            print(line)

    # Parse version from output
    version_string = None
    for line in result.stdout.splitlines():
        if line.startswith("VERSION:"):
            version_string = line.split(":", 1)[1]
            break

    # Set version attribute on the built artifact
    dist_artifact = DIST_DIR / art_name
    if version_string:
        set_version(dist_artifact, version_string)

    # Cache versioned builds
    if version and version_string:
        add_to_cache(lang, version, dist_artifact)
        print(f"Cached {art_name} at {cache_path(lang, version)}")

    return dist_artifact


def build_all() -> None:
    """Build all languages from languages.txt."""
    languages = load_languages()
    for lang in languages:
        try:
            build_single(lang)
        except Exception as e:
            print(f"Error building {lang}: {e}", file=sys.stderr)


# --- Install ---
def install_single(lang: str, version: Optional[str] = None) -> Path:
    """
    Build and install a single language grammar.
    Returns the path to the installed artifact.
    """
    install_dir = Path(os.environ.get("INSTALL_DIR", DEFAULT_INSTALL_DIR))

    # Build (will use cache if available for versioned builds)
    build_single(lang, version)

    # Copy to install directory
    art_name = artifact_name(lang)
    install_dir.mkdir(parents=True, exist_ok=True)

    dist_artifact = DIST_DIR / art_name
    install_artifact = install_dir / art_name
    shutil.copy2(dist_artifact, install_artifact)

    # Copy version attribute
    dist_version = get_version(dist_artifact)
    if dist_version:
        set_version(install_artifact, dist_version)

    print(f"Installed {art_name} to {install_dir}")
    return install_artifact


def install_all() -> None:
    """Build and install all languages from languages.txt."""
    languages = load_languages()
    for lang in languages:
        try:
            install_single(lang)
        except Exception as e:
            print(f"Error installing {lang}: {e}", file=sys.stderr)


def show_version(lang: str) -> Optional[str]:
    """
    Show the version of an installed grammar.
    Returns the version string or None if not installed.
    """
    install_dir = Path(os.environ.get("INSTALL_DIR", DEFAULT_INSTALL_DIR))
    art_name = artifact_name(lang)
    installed_artifact = install_dir / art_name

    if installed_artifact.exists() and has_version(installed_artifact):
        return get_version(installed_artifact)
    return None


# --- CLI ---
def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Tree-sitter grammar builder and installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s build python
  %(prog)s build --version v0.23.2 python
  %(prog)s build                    # Build all languages
  %(prog)s install python
  %(prog)s install                  # Install all languages
  %(prog)s version python

Environment:
  INSTALL_DIR    Override default install directory (~/.emacs.d/tree-sitter)

Caching:
  Versioned builds (--version) are cached and reused on subsequent builds.
  HEAD builds (no --version) always rebuild from the latest commit.
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Build command
    build_parser = subparsers.add_parser("build", help="Build grammar(s)")
    build_parser.add_argument(
        "--version", "-v",
        help="Specify version (git tag or commit)",
    )
    build_parser.add_argument(
        "language",
        nargs="?",
        help="Language to build (all if omitted)",
    )

    # Install command
    install_parser = subparsers.add_parser("install", help="Build and install grammar(s)")
    install_parser.add_argument(
        "--version", "-v",
        help="Specify version (git tag or commit)",
    )
    install_parser.add_argument(
        "language",
        nargs="?",
        help="Language to install (all if omitted)",
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show installed version")
    version_parser.add_argument(
        "language",
        help="Language to check",
    )

    return parser.parse_args(args)


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: langman.py <command> [options] [language]", file=sys.stderr)
        print("Commands: build, install, version", file=sys.stderr)
        print("Use --help for more information.", file=sys.stderr)
        return 1

    args = parse_args(sys.argv[1:])

    try:
        if args.command == "build":
            if args.version and not args.language:
                print("Error: --version requires a language", file=sys.stderr)
                return 1
            if args.language:
                build_single(args.language, args.version)
            else:
                if args.version:
                    print("Error: --version is not valid for batch builds", file=sys.stderr)
                    return 1
                build_all()

        elif args.command == "install":
            if args.version and not args.language:
                print("Error: --version requires a language", file=sys.stderr)
                return 1
            if args.language:
                install_single(args.language, args.version)
            else:
                install_all()

        elif args.command == "version":
            version = show_version(args.language)
            if version:
                print(version)
            else:
                print("not installed")
                return 1

        return 0

    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
