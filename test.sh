#!/usr/bin/env sh
total=0
pass=0

for i in testcases/*.py; do
    filename="$(basename $i)"
    if [[ "$filename" != "__init__.py" ]]; then
        ((total++))
        testcase="${filename%.*}"
        ./run.py -v "$testcase" &>/dev/null
        if (( $? == 0 )); then
            ((pass++))
        else
            echo "$testcase: failed"
        fi
    fi
done

echo "$pass/$total tests passed"
