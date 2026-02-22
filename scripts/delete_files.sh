#!/bin/bash

IFS=$'\n'
for f in $(cat dfiles) ; do
    if [[ $f == *".jpg"* ]]; then
        rm "$f"
    fi
done
