#!/usr/bin/env bash

set -u
set -e

lang=$1
topdir="$PWD"

if [ "$(uname)" == "Darwin" ]
then
    soext="dylib"
elif uname | grep -q "MINGW" > /dev/null
then
    soext="dll"
else
    soext="so"
fi

echo "Building ${lang}"

### Retrieve sources

site="https://github.com"
org="tree-sitter"
repo="tree-sitter-${lang}"
sourcedir="src"
branch=""

# Please keep this case analysis sorted alphabetically for ease of maintenance and readability. Note
# that you may want to add a corresponding entry to the `languages` array in the batch.sh script.
case "${lang}" in
    "ada")
        org="briot"
        ;;
    "astro")
        org="virchau13"
        ;;
    "bison")
        site="https://gitlab.com"
        org="btuin2"
        ;;
    "c3")
        org="c3lang"
        ;;
    "clojure")
        org="sogaiu"
        ;;
    "cpp")
        branch="v0.22.0"
        ;;
    "cmake")
        org="uyha"
        ;;
    "cylc")
        org="elliotfontaine"
        ;;
    "dart")
        org="ast-grep"
        ;;
    "dockerfile")
        org="camdencheek"
        ;;
    "doxygen")
        org="tree-sitter-grammars"
        ;;
    "elisp")
        org="Wilfred"
        ;;
    "elixir")
        org="elixir-lang"
        ;;
    "erlang")
        org="WhatsApp"
        ;;
    "glsl")
        org="tree-sitter-grammars"
        ;;
    "gomod")
        org="camdencheek"
        repo="tree-sitter-go-mod"
        ;;
    "gowork")
        org="omertuc"
        repo="tree-sitter-go-work"
        ;;
    "gpr")
        org="brownts"
        ;;
    "heex")
        org="phoenixframework"
        ;;
    "janet-simple")
        org="sogaiu"
        ;;
    "kotlin")
        org="fwcd"
        ;;
    "lua")
        org="tree-sitter-grammars"
        ;;
    "magik")
        org="krn-robin"
        ;;
    "make")
        org="tree-sitter-grammars"
        ;;
    "markdown")
        org="tree-sitter-grammars"
        sourcedir="tree-sitter-markdown/src"
        ;;
    "markdown-inline")
        org="tree-sitter-grammars"
        repo="tree-sitter-markdown"
        sourcedir="tree-sitter-markdown-inline/src"
        ;;
    "nix")
        org="nix-community"
        ;;
    "org")
        org="milisims"
        ;;
    "perl")
        org="ganezdragon"
        ;;
    "php")
        sourcedir='php/src'
        ;;
    "proto")
        org="mitchellh"
        ;;
    "scss")
        org="tree-sitter-grammars"
        ;;
    "sdml")
        org="sdm-lang"
        ;;
    "souffle")
        org="chaosite"
        ;;
    "sql")
        org="DerekStride"
        branch="gh-pages"
        ;;
    "surface")
        org="connorlay"
        ;;
    "svelte")
        org="Himujjal"
        ;;
    "toml")
        org="tree-sitter-grammars"
        ;;
    "tsx")
        repo="tree-sitter-typescript"
        sourcedir="tsx/src"
        ;;
    "typescript")
        sourcedir="typescript/src"
        ;;
    "typst")
        org="uben0"
        ;;
    "vala")
        org="vala-lang"
        ;;
    "verilog")
        org="gmlarumbe"
        ;;
    "vhdl")
        org="alemuller"
        ;;
    "wgsl")
        org="mehmetoguzderin"
        ;;
    "yaml")
        org="tree-sitter-grammars"
        ;;
    "zig")
        org="maxxnino"
        ;;
esac

if [ -z "$branch" ]
then
    git clone "${site}/${org}/${repo}.git" \
       --depth 1 --quiet "${lang}"
else
    git clone "${site}/${org}/${repo}.git" \
        --single-branch --depth 1 --branch "${branch}" --quiet "${lang}"
fi
# We have to go into the source directory to compile, because some
# C files refer to files like "../../common/scanner.h".
cd "${lang}/${sourcedir}"

### Build

cc -march=native -O3 -fPIC -c -I. parser.c
# Compile scanner.c.
if test -f scanner.c
then
    cc -march=native -O3 -fPIC -c -I. scanner.c
fi
# Compile scanner.cc.
if test -f scanner.cc
then
    c++ -march=native -O3 -fPIC -I. -c scanner.cc
fi
# Link.
if test -f scanner.cc
then
    c++ -march=native -O3 -fPIC -shared *.o -o "libtree-sitter-${lang}.${soext}"
else
    cc -march=native -O3 -fPIC -shared *.o -o "libtree-sitter-${lang}.${soext}"
fi

### Copy out

# use default dist location if INSTALL_DIR is unset or empty.
if [ -n "${INSTALL_DIR-}" ]; then
    dist_dir="${INSTALL_DIR}"
else
    dist_dir="${topdir}/dist"
fi

echo "Copying libtree-sitter-${lang}.${soext} to ${dist_dir}"
mkdir -p "${dist_dir}"
cp "libtree-sitter-${lang}.${soext}" "${dist_dir}"
cd "${topdir}"
rm -rf "${lang}"
