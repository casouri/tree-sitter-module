#!/bin/bash

languages=(
    'c'
    'json'
    'go'
    'html'
    'javascript'
    'css'
    'python'
)

for language in "${languages[@]}"
do
    ./build-new.sh $language
done
