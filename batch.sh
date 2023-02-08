#!/usr/bin/env bash

set -u
set -e

languages=(
    'bash'
    'c'
    'c-sharp'
    'cmake'
    'cpp'
    'css'
    'dockerfile'
    'elixir'
    'glsl'
    'go'
    'go-mod'
    'heex'
    'html'
    'java'
    'javascript'
    'json'
    'julia'
    'make'
    'markdown'
    'org'
    'perl'
    'proto'
    'python'
    'ruby'
    'rust'
    'sql'
    'toml'
    'tsx'
    'typescript'
    'verilog'
    'vhdl'
    'wgsl'
    'yaml'
)

if [ -z "${JOBS:-}" ]
then
    for language in "${languages[@]}"
    do
        ./build.sh "${language}"
    done
else
    printf "%s\n" "${languages[@]}" | xargs -P"${JOBS}" -n1 ./build.sh
fi
