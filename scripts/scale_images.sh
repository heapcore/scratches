#!/bin/bash
files=*.tif
minimumWidth=2000
minimumHeight=2000

for f in $files
do
    imageWidth=$(identify -format "%w" "$f")
    imageHeight=$(identify -format "%h" "$f")

    if [ "$imageWidth" -gt "$minimumWidth" ] || [ "$imageHeight" -gt "$minimumHeight" ]; then
        mogrify -resize ''"$minimumWidth"x"$minimumHeight"'' -format jpg $f
    else
        mogrify -format jpg $f
    fi
done
