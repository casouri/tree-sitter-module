#!/usr/bin/env bash

set -u
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

lang=$1

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

source "${SCRIPT_DIR}/lang-config.sh"
get_lang_config "$lang"

if [ -z "$LANG_BRANCH" ]
then
    git clone "${LANG_SITE}/${LANG_ORG}/${LANG_REPO}.git" \
       --depth 1 --quiet "${lang}"
else
    git clone "${LANG_SITE}/${LANG_ORG}/${LANG_REPO}.git" \
        --single-branch --branch "${LANG_BRANCH}" --quiet "${lang}"
fi
# We have to go into the source directory to compile, because some
# C files refer to files like "../../common/scanner.h".
cd "${lang}/${LANG_SOURCEDIR}"

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

dist_dir="${INSTALL_DIR:-${SCRIPT_DIR}/dist}"

echo "Copying libtree-sitter-${lang}.${soext} to ${dist_dir}"
mkdir -p "${dist_dir}"
cp "libtree-sitter-${lang}.${soext}" "${dist_dir}"
cd -
rm -rf "${lang}"
