#!/usr/bin/env python3
"""Tree-sitter grammar builder and installer."""

# --- Imports (stdlib only) ---
import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# --- Constants ---
SCRIPT_DIR = Path(__file__).parent.resolve()
CACHE_DIR = SCRIPT_DIR / ".cache"
DIST_DIR = SCRIPT_DIR / "dist"
DEFAULT_INSTALL_DIR = Path.home() / ".emacs.d" / "tree-sitter"

# --- Language Configurations ---
# Dict of overrides, default is github.com/tree-sitter/tree-sitter-{lang}
LANG_CONFIGS: dict[str, dict] = {
    "ada": {"org": "briot"},
    "bison": {"site": "https://gitlab.com", "org": "btuin2"},
    "clojure": {"org": "sogaiu"},
    "cmake": {"org": "uyha"},
    "dart": {"org": "ast-grep"},
    "dockerfile": {"org": "camdencheek"},
    "doxygen": {"org": "tree-sitter-grammars"},
    "elisp": {"org": "Wilfred"},
    "elixir": {"org": "elixir-lang"},
    "erlang": {"org": "WhatsApp"},
    "glsl": {"org": "tree-sitter-grammars"},
    "gomod": {"org": "camdencheek", "repo": "tree-sitter-go-mod"},
    "gpr": {"org": "brownts"},
    "heex": {"org": "phoenixframework"},
    "janet-simple": {"org": "sogaiu"},
    "kotlin": {"org": "fwcd"},
    "lua": {"org": "tree-sitter-grammars"},
    "magik": {"org": "krn-robin"},
    "make": {"org": "tree-sitter-grammars"},
    "markdown": {
        "org": "tree-sitter-grammars",
        "repo": "tree-sitter-markdown",
        "source_dir": "tree-sitter-markdown/src",
    },
    "markdown_inline": {
        "org": "tree-sitter-grammars",
        "repo": "tree-sitter-markdown",
        "source_dir": "tree-sitter-markdown-inline/src",
    },
    "nix": {"org": "nix-community"},
    "org": {"org": "milisims"},
    "perl": {"org": "ganezdragon"},
    "php": {"source_dir": "php/src"},
    "proto": {"org": "mitchellh"},
    "scss": {"org": "tree-sitter-grammars"},
    "souffle": {"org": "chaosite"},
    "sql": {"org": "DerekStride", "branch": "gh-pages"},
    "surface": {"org": "connorlay"},
    "toml": {"org": "tree-sitter-grammars"},
    "tsx": {"repo": "tree-sitter-typescript", "source_dir": "tsx/src"},
    "typescript": {"source_dir": "typescript/src"},
    "typst": {"org": "uben0"},
    "vala": {"org": "vala-lang"},
    "verilog": {"org": "gmlarumbe"},
    "vhdl": {"org": "alemuller"},
    "wgsl": {"org": "mehmetoguzderin"},
    "yaml": {"org": "tree-sitter-grammars"},
    "zig": {"org": "maxxnino"},
}


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


# --- Language Config ---
@dataclass
class LangConfig:
    """Configuration for a tree-sitter language grammar."""

    name: str
    site: str = "https://github.com"
    org: str = "tree-sitter"
    repo: Optional[str] = None
    source_dir: str = "src"
    branch: Optional[str] = None

    @property
    def effective_repo(self) -> str:
        """Get the actual repository name (default: tree-sitter-{name})."""
        return self.repo if self.repo else f"tree-sitter-{self.name}"

    @property
    def clone_url(self) -> str:
        """Get the full clone URL."""
        return f"{self.site}/{self.org}/{self.effective_repo}.git"


def get_lang_config(lang: str) -> LangConfig:
    """Get the configuration for a language."""
    overrides = LANG_CONFIGS.get(lang, {})
    return LangConfig(
        name=lang,
        site=overrides.get("site", "https://github.com"),
        org=overrides.get("org", "tree-sitter"),
        repo=overrides.get("repo"),
        source_dir=overrides.get("source_dir", "src"),
        branch=overrides.get("branch"),
    )


def load_languages() -> list[str]:
    """Load the list of supported languages from languages.txt."""
    languages_file = SCRIPT_DIR / "languages.txt"
    languages = []
    with open(languages_file) as f:
        for line in f:
            lang = line.strip()
            if lang:
                languages.append(lang)
    return languages


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
    Build a single language grammar.
    Returns the path to the built artifact in dist/.
    """
    art_name = artifact_name(lang)

    # Check cache if version specified
    if version and is_cached(lang, version):
        print(f"Using cached {lang} {version}")
        result = get_from_cache(lang, version, DIST_DIR)
        if result:
            return result

    print(f"Building {lang}" + (f" ({version})" if version else ""))

    # Get language configuration
    cfg = get_lang_config(lang)

    # Create temp directory for build
    build_dir = Path(tempfile.mkdtemp())
    original_cwd = os.getcwd()

    try:
        os.chdir(build_dir)

        # Clone repository
        if version:
            # Full clone for versioned build, then checkout
            subprocess.run(
                ["git", "clone", cfg.clone_url, "--quiet", lang],
                check=True,
            )
            subprocess.run(
                ["git", "-C", lang, "checkout", version, "--quiet"],
                check=True,
            )
        elif cfg.branch:
            # Clone specific branch
            subprocess.run(
                [
                    "git", "clone", cfg.clone_url,
                    "--single-branch", "--branch", cfg.branch,
                    "--quiet", lang,
                ],
                check=True,
            )
        else:
            # Shallow clone of default branch
            subprocess.run(
                ["git", "clone", cfg.clone_url, "--depth", "1", "--quiet", lang],
                check=True,
            )

        # Get commit SHA for version string
        result = subprocess.run(
            ["git", "-C", lang, "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        # Navigate to source directory
        src_dir = build_dir / lang / cfg.source_dir
        os.chdir(src_dir)

        # Build: compile C files
        subprocess.run(["cc", "-fPIC", "-c", "-I.", "parser.c"], check=True)

        # Compile scanner if present
        has_scanner_c = (src_dir / "scanner.c").exists()
        has_scanner_cc = (src_dir / "scanner.cc").exists()

        if has_scanner_c:
            subprocess.run(["cc", "-fPIC", "-c", "-I.", "scanner.c"], check=True)
        if has_scanner_cc:
            subprocess.run(["c++", "-fPIC", "-I.", "-c", "scanner.cc"], check=True)

        # Link
        if has_scanner_cc:
            subprocess.run(
                ["c++", "-fPIC", "-shared"] + list(src_dir.glob("*.o")) + ["-o", art_name],
                check=True,
            )
        else:
            subprocess.run(
                ["cc", "-fPIC", "-shared"] + list(src_dir.glob("*.o")) + ["-o", art_name],
                check=True,
            )

        # Create version string
        version_string = version if version else f"HEAD@{commit_sha}"

        # Set version attribute on artifact
        built_artifact = src_dir / art_name
        set_version(built_artifact, version_string)

        # Copy to dist
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        dist_artifact = DIST_DIR / art_name
        shutil.copy2(built_artifact, dist_artifact)
        set_version(dist_artifact, version_string)
        print(f"Copied {art_name} to {DIST_DIR}")

        # Cache if versioned
        if version:
            add_to_cache(lang, version, built_artifact)
            print(f"Cached {art_name} at {cache_path(lang, version)}")

        return dist_artifact

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(build_dir, ignore_errors=True)


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
