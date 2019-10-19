#!/usr/bin/env sh
for i in testcases/*.py; do
    filename="$(basename $i)"
    if [[ "$filename" != "__init__.py" ]]; then
        ./run.py -v "${filename%.*}"
    fi
done
