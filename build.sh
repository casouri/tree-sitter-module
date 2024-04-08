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
    "bison")
        site="https://gitlab.com"
        org="btuin2"
        ;;
    "clojure")
        org="sogaiu"
        ;;
    "cmake")
        org="uyha"
        ;;
    "dart")
        org="ast-grep"
        ;;
    "dockerfile")
        org="camdencheek"
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
        org="theHamsta"
        ;;
    "gomod")
        org="camdencheek"
        repo="tree-sitter-go-mod"
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
        org="MunifTanjim"
        ;;
    "magik")
        org="krn-robin"
        ;;
    "make")
        org="alemuller"
        ;;
    "markdown")
        org="ikatyang"
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
        org="serenadeai"
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
    "toml")
        org="ikatyang"
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
        org="ikatyang"
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
        --single-branch --branch "${branch}" --quiet "${lang}"
fi
# We have to go into the source directory to compile, because some
# C files refer to files like "../../common/scanner.h".
cd "${lang}/${sourcedir}"

### Build

cc -fPIC -c -I. parser.c
# Compile scanner.c.
if test -f scanner.c
then
    cc -fPIC -c -I. scanner.c
fi
# Compile scanner.cc.
if test -f scanner.cc
then
    c++ -fPIC -I. -c scanner.cc
fi
# Link.
if test -f scanner.cc
then
    c++ -fPIC -shared *.o -o "libtree-sitter-${lang}.${soext}"
else
    cc -fPIC -shared *.o -o "libtree-sitter-${lang}.${soext}"
fi

### Copy out
if [[ -n "$INSTALL_DIR" ]]; then
    dist_dir="$INSTALL_DIR"
    echo "Copying libtree-sitter-${lang}.${soext} to ${dist_dir}"
else
  dist_dir="${topdir}/dist"
fi

mkdir -p "${dist_dir}"
cp "libtree-sitter-${lang}.${soext}" "${dist_dir}"
cd "${topdir}"
rm -rf "${lang}"
