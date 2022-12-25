#!/bin/bash

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

for language in "${languages[@]}"
do
    ./build.sh "${language}"
done
