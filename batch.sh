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

if [ -e dist ]
then
    rm -rf dist
fi

for language in "${languages[@]}"
do
    ./build.sh $language
done
