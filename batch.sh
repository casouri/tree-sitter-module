#!/bin/bash

set -u
set -e

languages=(
    'c'
    'c-sharp'
    'cpp'
    'css'
    'elixir'
    'go'
    'heex'
    'html'
    'javascript'
    'json'
    'python'
    'rust'
    'typescript'
)

for language in "${languages[@]}"
do
    ./build.sh "${language}"
done
