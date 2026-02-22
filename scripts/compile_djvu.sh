#!/bin/bash
losslevel=100
output_name="book.djvu"

for f in *.tif; do
    name="${f%.*}"
    cjb2 -losslevel $losslevel $f $name.djvu
done

count=0
for f in *.djvu; do
    if [ "$count" -eq 0 ]; then
        cp $f $output_name
    else
        djvm -i $output_name $f
    fi
    (( count++ ))
done
