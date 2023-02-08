#!/usr/bin/env bash

set -u
set -e

if [ -z "${JOBS:-}" ]
then
    JOBS=$(nproc) || JOBS=1
fi

xargs -r -d '\n' -a "$PWD/languages.txt" -n1 -P"$JOBS" "$PWD/build.sh"
