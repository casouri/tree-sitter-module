#!/usr/bin/env bash

set -u
set -e

languages=(
    'bash'
    'bison'
    'c'
    'c-sharp'
    'clojure'
    'cmake'
    'cpp'
    'css'
    'dart'
    'dockerfile'
    'elisp'
    'elixir'
    'erlang'
    'glsl'
    'go'
    'gomod'
    'heex'
    'html'
    'janet-simple'
    'java'
    'javascript'
    'json'
    'julia'
    'kotlin'
    'lua'
    'make'
    'markdown'
    'org'
    'perl'
    'proto'
    'python'
    'ruby'
    'rust'
    'scala'
    'scss'
    'souffle'
    'sql'
    'surface'
    'toml'
    'tsx'
    'typescript'
    'typst'
    'vala'
    'verilog'
    'vhdl'
    'wgsl'
    'yaml'
    'zig'
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
