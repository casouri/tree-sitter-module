#!/bin/bash

set -u
set -e

languages=(
    'c'
    'c-sharp'
    'cmake'
    'cpp'
    'css'
    'dockerfile'
    'elixir'
    'go'
    'heex'
    'html'
    'javascript'
    'json'
    'python'
    'rust'
    'tsx'
    'typescript'
)

for language in "${languages[@]}"
do
    ./build.sh "${language}"
done
