#!/bin/bash
echo "Starting kongfig push to kong..."
set -x
for FILE in `ls`; do
    echo "Applying `pwd`/$FILE"
    kongfig apply --path "`pwd`/$FILE" --host kong:8001
done
