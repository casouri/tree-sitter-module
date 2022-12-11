#!/bin/bash

lang=$1
org="tree-sitter"

if [ "${lang}" == "elixir" ]
then
    org="elixir-lang"
fi

if [ "${lang}" == "heex" ]
then
    org="phoenixframework"
fi

if [ $(uname) == "Darwin" ]
then
    soext="dylib"
else
    soext="so"
fi

echo "Building ${lang}"

repo="${lang}"
if [ "${lang}" == "tsx" ]
then
    repo="typescript"
fi

# Retrieve sources.
if [ ! -e "tree-sitter-${repo}" ]
then
    git clone "https://github.com/${org}/tree-sitter-${repo}.git" \
        --depth 1 --quiet
fi

if [ "${lang}" == "tsx" ]
then
    lang="typescript/tsx"
fi

if [ "${lang}" == "typescript" ]
then
    lang="typescript/typescript"
fi
cp tree-sitter-lang.in "tree-sitter-${lang}/src"
cp emacs-module.h "tree-sitter-${lang}/src"
cp "tree-sitter-${lang}/grammar.js" "tree-sitter-${lang}/src"
cd "tree-sitter-${lang}/src"

if [ "${lang}" == "typescript/tsx" ]
then
    lang="tsx"
fi

if [ "${lang}" == "typescript/typescript" ]
then
    lang="typescript"
fi

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
    c++ -fPIC -shared *.o -o "libtree-sitter-${lang}.${soext}"
else
    cc -fPIC -shared *.o -o "libtree-sitter-${lang}.${soext}"
fi

# Copy out.

if [ "${lang}" == "tsx" ]
then
    cp "libtree-sitter-${lang}.${soext}" ..
    cd ..
fi

if [ "${lang}" == "typescript" ]
then
    cp "libtree-sitter-${lang}.${soext}" ..
    cd ..
fi

mkdir -p ../../dist
cp "libtree-sitter-${lang}.${soext}" ../../dist
cd ../../
if [ "${lang}" == "tsx" ]
then
    rm -rf "tree-sitter-typescript"
else
    rm -rf "tree-sitter-${lang}"
fi

