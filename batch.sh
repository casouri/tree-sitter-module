#!/bin/bash

languages=(
    'c'
    'json'
    'go'
    'html'
    'javascript'
    'css'
    'python'
    'typescript'
    'c-sharp'
)

for language in "${languages[@]}"
do
    ./build.sh $language
done
