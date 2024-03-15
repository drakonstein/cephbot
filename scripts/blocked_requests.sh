#!/bin/bash
args=$(/bin/sh $(dirname $0)/common_args.sh $@)
if (( $? != 0 )); then
  echo "$args"
  exit
fi

output=$(ceph $args health detail | grep 'ops are blocked' | sort -nrk6 | sed 's/ ops/+ops/' | sed 's/ sec/+sec/' | column -t -s'+')
if [[ -z "$output" ]]; then
    echo "No blocked requests"
else
    echo "$output" | grep -v 'on osd'
    echo "$output" | grep -Eo osd.[0-9]+ | sort -n | uniq -c | grep -v ' 1 '
    echo "$output" | grep 'on osd'
fi
