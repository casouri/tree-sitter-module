#!/usr/bin/env bash

set -u
set -e

# List of supported languages. Please keep this array sorted alphabetically for ease of maintenance
# and readability.
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
    'doxygen'
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
    'magik'
    'make'
    'markdown'
    'org'
    'perl'
    'php'
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
