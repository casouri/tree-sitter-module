#!/usr/bin/env bash

set -u
set -e

# List of supported languages. Please keep this array sorted alphabetically for ease of maintenance
# and readability.
languages=(
    'ada'
    'astro'
    'bash'
    'bison'
    'c'
    'c3'
    'c-sharp'
    'clojure'
    'cmake'
    'cpp'
    'css'
    'cylc'
    'dart'
    'dockerfile'
    'doxygen'
    'elisp'
    'elixir'
    'erlang'
    'glsl'
    'go'
    'gomod'
    'gowork'
    'gpr'
    'haskell'
    'heex'
    'html'
    'janet-simple'
    'java'
    'javascript'
    'jsdoc'
    'json'
    'julia'
    'kotlin'
    'lua'
    'magik'
    'make'
    'markdown'
    'markdown-inline'
    'nix'
    'org'
    'perl'
    'php'
    'proto'
    'python'
    'ruby'
    'rust'
    'scala'
    'scss'
    'sdml'
    'souffle'
    'sql'
    'surface'
    'svelte'
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
