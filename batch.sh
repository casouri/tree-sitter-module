#!/bin/bash

set -u
set -e

languages=(
    'c'
    'cmake'
    'cpp'
    'css'
    'c-sharp'
    'dockerfile'
    'go'
    'html'
    'javascript'
    'json'
    'python'
    'rust'
    'tsx'
    'typescript'
    'elixir'
    'heex'
)

for language in "${languages[@]}"
do
    ./build.sh "${language}"
done
