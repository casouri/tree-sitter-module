#!/bin/bash

set -u
set -e

if [ "$(uname)" = "Darwin" ]
then
    soext="dylib"
elif uname | grep -q "MINGW" > /dev/null
then
    soext="dll"
else
    soext="so"
fi

# Target language to build a parser for
lang=$1
# Base directory containing this project
topdir="$PWD"
# Base directory to clone the parser repository to
repodir="$topdir/repos"
# Base directory to copy parser libraries to after building
parserdir="$topdir/dist"
# Filename of the parser library for ${lang}
langparser="libtree-sitter-$lang.$soext"

echo "Building ${lang}"

### Retrieve sources

# GitHub organisation hosting the parser for ${lang}
org="tree-sitter"
# GitHub repository in ${org} hosting the parser for ${lang}
repo="tree-sitter-${lang}"

# Subdirectory within ${sourcedir} containing parser source files for ${lang}
parsersubdir="src"
# Subdirectory within ${sourcedir} containing a grammar.js file for ${lang}
grammarsubdir=""

case "${lang}" in
    "dockerfile")
        org="camdencheek"
        ;;
    "cmake")
        org="uyha"
        ;;
    "typescript")
        parsersubdir="typescript/src"
        grammarsubdir="typescript"
        ;;
    "tsx")
        repo="tree-sitter-typescript"
        parsersubdir="tsx/src"
        grammarsubdir="tsx"
        ;;
    "elixir")
        org="elixir-lang"
        ;;
    "heex")
        org="phoenixframework"
        ;;
    "glsl")
        org="theHamsta"
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
    "proto")
        org="mitchellh"
        ;;
    "sql")
        org="m-novikov"
        ;;
    "toml")
        org="ikatyang"
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
esac

# Local directory to clone parser repository to
sourcedir="${repodir}/${org}/${repo}"

if [ -e "$sourcedir" ]
then
    # Already cloned, check if needs to be updated and rebuilt.
    git -C "${sourcedir}" remote update
    if [ -n "$(git -C "${sourcedir}" diff origin --numstat)" ]
    then
        git -C "${sourcedir}" merge --ff-only origin
        # Removing the existing parser from the previous build to ensure if
        # building it fails we don't just keep using an out of date parser.
        rm "${parserdir}/${langparser}"
    elif [ -e "${parserdir}/${langparser}" ]
    then
        echo "Skipping ${lang}" >&2
        exit 0
    fi
else
    git clone "https://github.com/${org}/${repo}.git" --depth 1 --quiet "${sourcedir}"
fi

# We have to go into the source directory to compile, because some
# C files refer to files like "../../common/scanner.h".
cd "${sourcedir}/${parsersubdir}"

# Ensure the grammar.js file exists for the parser build.
if ! [ -e grammar.js ]
then
    ln -sf "${sourcedir}/${grammarsubdir}"/grammar.js ./
fi

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
    c++ -fPIC -shared *.o -o "${langparser}"
else
    cc -fPIC -shared *.o -o "${langparser}"
fi

### Copy out

mkdir -p "${parserdir}"
cp "${langparser}" "${parserdir}"
