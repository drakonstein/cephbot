#!/bin/bash

[[ ! -z "$1" ]] && conf="--conf $1" || conf=
[[ ! -z "$2" ]] && user="--name $2" || user=
[[ ! -z "$3" ]] && keyring="--keyring $3" || keyring=
output=$(ceph $conf $user $keyring health detail | grep 'ops are blocked' | sort -nrk6 | sed 's/ ops/+ops/' | sed 's/ sec/+sec/' | column -t -s'+')
if [[ -z "$output" ]]; then
    echo "No blocked requests"
else
    echo "$output" | grep -v 'on osd'
    echo "$output" | grep -Eo osd.[0-9]+ | sort -n | uniq -c | grep -v ' 1 '
    echo "$output" | grep 'on osd'
fi
