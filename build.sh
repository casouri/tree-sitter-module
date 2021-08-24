#!/bin/bash

lang=$1

if [ $(uname) == "Darwin" ]
then
    soext="dylib"
else
    soext="so"
fi

# Retrieve sources.
git clone "https://github.com/tree-sitter/tree-sitter-${lang}.git" \
    --depth 1
cp tree-sitter-lang.in "tree-sitter-${lang}/src"
cp emacs-module.h "tree-sitter-${lang}/src"
cp "tree-sitter-${lang}/grammar.js" "tree-sitter-${lang}/src"
cd "tree-sitter-${lang}/src"

# The dynamic module's c source.
sed "s/LANG/${lang}/g" tree-sitter-lang.in > "tree-sitter-${lang}.c"
# Dump file of grammar definition to be included in the module.
xxd -i < grammar.js > grammar.js.dump

# Build.
cc -c -Itree_sitter *.c
if test -f *.cc
then
    c++ -c *.cc
    c++ -shared *.o -o "tree-sitter-${lang}.${soext}"
else
    cc -shared *.o -o "tree-sitter-${lang}.${soext}"
fi

# Copy out.

mkdir -p ../../dist
cp "tree-sitter-${lang}.${soext}" ../../dist
cd ../../
rm -rf "tree-sitter-${lang}"
