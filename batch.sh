#!/usr/bin/env bash

set -u
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Load supported languages from shared file
languages=()
while IFS= read -r lang || [[ -n "$lang" ]]; do
    [[ -n "$lang" ]] && languages+=("$lang")
done < "${SCRIPT_DIR}/languages.txt"

if [ -z "${JOBS:-}" ]
then
    for language in "${languages[@]}"
    do
        "${SCRIPT_DIR}/build.sh" "${language}"
    done
else
    printf "%s\n" "${languages[@]}" | xargs -P"${JOBS}" -n1 "${SCRIPT_DIR}/build.sh"
fi
