#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CACHE_DIR="${SCRIPT_DIR}/.cache"
DEFAULT_INSTALL_DIR="${HOME}/.emacs.d/tree-sitter"

# Load supported languages from shared file
LANGUAGES=()
while IFS= read -r lang || [[ -n "$lang" ]]; do
    [[ -n "$lang" ]] && LANGUAGES+=("$lang")
done < "${SCRIPT_DIR}/languages.txt"

# Detect platform extension
detect_platform() {
    if [ "$(uname)" == "Darwin" ]; then
        echo "dylib"
    elif uname | grep -q "MINGW"; then
        echo "dll"
    else
        echo "so"
    fi
}

# Detect xattr method: "macos", "linux", or "none"
detect_xattr_method() {
    if [ "$(uname)" == "Darwin" ]; then
        echo "macos"
    elif command -v setfattr &>/dev/null && command -v getfattr &>/dev/null; then
        echo "linux"
    else
        echo "none"
    fi
}

# Set version attribute on file
set_version_attr() {
    local file="$1"
    local version="$2"
    local method
    method=$(detect_xattr_method)

    case "$method" in
        macos) xattr -w user.version "$version" "$file" ;;
        linux) setfattr -n user.version -v "$version" "$file" ;;
        none)  echo "$version" > "${file}.version" ;;
    esac
}

# Get version attribute from file (prints to stdout)
get_version_attr() {
    local file="$1"
    local method
    method=$(detect_xattr_method)

    case "$method" in
        macos) xattr -p user.version "$file" 2>/dev/null ;;
        linux) getfattr -n user.version --only-values "$file" 2>/dev/null ;;
        none)  cat "${file}.version" 2>/dev/null ;;
    esac
}

# Check if version attribute exists
has_version_attr() {
    local file="$1"
    local method
    method=$(detect_xattr_method)

    case "$method" in
        macos) xattr -p user.version "$file" &>/dev/null ;;
        linux) getfattr -n user.version "$file" &>/dev/null ;;
        none)  [ -f "${file}.version" ] ;;
    esac
}

# Source shared language configuration
source "${SCRIPT_DIR}/lang-config.sh"

# Build a single language
# Arguments: lang [version]
build_single() {
    local lang="$1"
    local version="${2:-}"
    local soext
    soext=$(detect_platform)
    local artifact="libtree-sitter-${lang}.${soext}"
    local topdir="$PWD"
    local dist_dir="${SCRIPT_DIR}/dist"

    # Check cache if version specified
    if [ -n "$version" ]; then
        local cache_path="${CACHE_DIR}/${lang}/${version}"
        if [ -f "${cache_path}/${artifact}" ] && has_version_attr "${cache_path}/${artifact}"; then
            echo "Using cached ${lang} ${version}"
            mkdir -p "${dist_dir}"
            cp "${cache_path}/${artifact}" "${dist_dir}/"
            set_version_attr "${dist_dir}/${artifact}" "$(get_version_attr "${cache_path}/${artifact}")"
            return 0
        fi
    fi

    echo "Building ${lang}${version:+ (${version})}"

    # Get language configuration
    get_lang_config "$lang"

    # Create temp directory for build
    local build_dir
    build_dir=$(mktemp -d)
    cd "$build_dir"

    # Clone repository
    if [ -n "$version" ]; then
        # Full clone for versioned build, then checkout
        git clone "${LANG_SITE}/${LANG_ORG}/${LANG_REPO}.git" --quiet "${lang}"
        cd "${lang}"
        git checkout "$version" --quiet
        cd ..
    elif [ -z "$LANG_BRANCH" ]; then
        git clone "${LANG_SITE}/${LANG_ORG}/${LANG_REPO}.git" \
            --depth 1 --quiet "${lang}"
    else
        git clone "${LANG_SITE}/${LANG_ORG}/${LANG_REPO}.git" \
            --single-branch --branch "${LANG_BRANCH}" --quiet "${lang}"
    fi

    # Get commit SHA for version string
    cd "${lang}"
    local commit_sha
    commit_sha=$(git rev-parse --short HEAD)
    cd "${LANG_SOURCEDIR}"

    # Build
    cc -fPIC -c -I. parser.c
    if test -f scanner.c; then
        cc -fPIC -c -I. scanner.c
    fi
    if test -f scanner.cc; then
        c++ -fPIC -I. -c scanner.cc
    fi

    # Link
    if test -f scanner.cc; then
        c++ -fPIC -shared *.o -o "${artifact}"
    else
        cc -fPIC -shared *.o -o "${artifact}"
    fi

    # Create version string
    local version_string
    if [ -n "$version" ]; then
        version_string="$version"
    else
        version_string="HEAD@${commit_sha}"
    fi

    # Set version attribute on artifact
    set_version_attr "${artifact}" "$version_string"

    # Copy to dist
    mkdir -p "${dist_dir}"
    cp "${artifact}" "${dist_dir}/"
    set_version_attr "${dist_dir}/${artifact}" "$version_string"
    echo "Copied ${artifact} to ${dist_dir}"

    # Cache if versioned
    if [ -n "$version" ]; then
        local cache_path="${CACHE_DIR}/${lang}/${version}"
        mkdir -p "${cache_path}"
        cp "${artifact}" "${cache_path}/"
        set_version_attr "${cache_path}/${artifact}" "$version_string"
        echo "Cached ${artifact} at ${cache_path}"
    fi

    # Cleanup
    cd "$topdir"
    rm -rf "$build_dir"
}

# Build all languages
build_all() {
    for lang in "${LANGUAGES[@]}"; do
        build_single "$lang"
    done
}

# Install a single language
# Arguments: lang [version]
install_single() {
    local lang="$1"
    local version="${2:-}"
    local install_dir="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
    local soext
    soext=$(detect_platform)
    local artifact="libtree-sitter-${lang}.${soext}"
    local dist_dir="${SCRIPT_DIR}/dist"

    # Build (will use cache if available for versioned builds)
    build_single "$lang" "$version"

    # Copy to install directory
    mkdir -p "${install_dir}"
    cp "${dist_dir}/${artifact}" "${install_dir}/"
    set_version_attr "${install_dir}/${artifact}" "$(get_version_attr "${dist_dir}/${artifact}")"
    echo "Installed ${artifact} to ${install_dir}"
}

# Install all languages
install_all() {
    for lang in "${LANGUAGES[@]}"; do
        install_single "$lang"
    done
}

# Show version of installed grammar
show_version() {
    local lang="$1"
    local install_dir="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
    local soext
    soext=$(detect_platform)
    local artifact="${install_dir}/libtree-sitter-${lang}.${soext}"

    if [ -f "$artifact" ] && has_version_attr "$artifact"; then
        get_version_attr "$artifact"
    else
        echo "not installed"
        return 1
    fi
}

# Print usage
usage() {
    cat <<EOF
Usage: langman.sh <command> [options] [language]

Commands:
  build [lang]                 Build grammar (all languages if lang omitted)
  build --version <ver> <lang> Build specific version (tag/commit)
  install [lang]               Build and install to ~/.emacs.d/tree-sitter (all if omitted)
  install --version <ver> <lang> Install specific version
  version <lang>               Print version of installed grammar

Options:
  --version <ver>    Specify version (git tag or commit) for build/install

Environment:
  INSTALL_DIR        Override default install directory (~/.emacs.d/tree-sitter)

Caching:
  Versioned builds (--version) are cached and reused on subsequent builds.
  HEAD builds (no --version) always rebuild from the latest commit.

Examples:
  langman.sh build python
  langman.sh build --version v0.23.2 python
  langman.sh build                    # Build all languages
  langman.sh install python
  langman.sh install                  # Install all languages
  langman.sh version python
EOF
}

# Main entry point
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    local cmd="$1"
    shift

    case "$cmd" in
        build)
            local version=""
            local lang=""

            # Parse arguments
            while [ $# -gt 0 ]; do
                case "$1" in
                    --version)
                        if [ $# -lt 2 ]; then
                            echo "Error: --version requires a value" >&2
                            exit 1
                        fi
                        version="$2"
                        shift 2
                        ;;
                    *)
                        lang="$1"
                        shift
                        ;;
                esac
            done

            if [ -n "$version" ] && [ -z "$lang" ]; then
                echo "Error: --version requires a language" >&2
                exit 1
            fi

            if [ -z "$lang" ]; then
                if [ -n "$version" ]; then
                    echo "Error: --version is not valid for batch builds" >&2
                    exit 1
                fi
                build_all
            else
                build_single "$lang" "$version"
            fi
            ;;
        install)
            local version=""
            local lang=""

            # Parse arguments
            while [ $# -gt 0 ]; do
                case "$1" in
                    --version)
                        if [ $# -lt 2 ]; then
                            echo "Error: --version requires a value" >&2
                            exit 1
                        fi
                        version="$2"
                        shift 2
                        ;;
                    *)
                        lang="$1"
                        shift
                        ;;
                esac
            done

            if [ -n "$version" ] && [ -z "$lang" ]; then
                echo "Error: --version requires a language" >&2
                exit 1
            fi

            if [ -z "$lang" ]; then
                install_all
            else
                install_single "$lang" "$version"
            fi
            ;;
        version)
            if [ $# -eq 0 ]; then
                echo "Error: version requires a language" >&2
                exit 1
            fi
            show_version "$1"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo "Error: Unknown command: $cmd" >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"
