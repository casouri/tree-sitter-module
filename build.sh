#!/bin/bash

lang=$1
org="tree-sitter"

function build() {
    local languagePath="$1"
    local languageName="$2"
    local buildDir="$PWD"
    
    cp tree-sitter-lang.in "tree-sitter-${languagePath}/src"
    cp emacs-module.h "tree-sitter-${languagePath}/src"
    cp "tree-sitter-${languagePath}/grammar.js" "tree-sitter-${languagePath}/src"
    cd "tree-sitter-${languagePath}/src" || exit 1

    # Build.
    cc -c -I. parser.c
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
	c++ -fPIC -shared ./*.o -o "libtree-sitter-${languageName}.${soext}"
    else
	cc -fPIC -shared ./*.o -o "libtree-sitter-${languageName}.${soext}"
    fi

    # Copy out
    mkdir -p "${buildDir}/dist"
    cp "libtree-sitter-${languageName}.${soext}" "${buildDir}/dist"
    cd "${buildDir}" || exit 1
}

if [ "${lang}" == "elixir" ]
then
    org="elixir-lang"
fi

if [ "${lang}" == "heex" ]
then
    org="phoenixframework"
fi

if [ "$(uname)" == "Darwin" ]
then
    soext="dylib"
else
    soext="so"
fi

echo "Building ${lang}"

# Retrieve sources.
git clone "https://github.com/${org}/tree-sitter-${lang}.git" \
    --depth 1 --quiet

if [ "${lang}" == "typescript" ]
then
    build "${lang}/tsx" "tsx"
    build "${lang}/typescript" "typescript"

    rm -rf "tree-sitter-typescript"
else
    build "${lang}" "${lang}"
    rm -rf "tree-sitter-${lang}"
fi

