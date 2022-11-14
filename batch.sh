#!/bin/bash

languages=(
    'c'
    'cpp'
    'css'
    'c-sharp'
    'go'
    'html'
    'javascript'
    'json'
    'python'
    'rust'
    'typescript'
    'elixir'
    'heex'
)

for language in "${languages[@]}"
do
    ./build.sh $language
done
