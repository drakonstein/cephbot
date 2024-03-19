#!/bin/bash
args=$(/bin/sh $(dirname $0)/common_args.sh $@)
if (( $? != 0 )); then
  echo "$args"
  exit
fi

output=$(ceph $args status | grep -A5 io | grep -v io)
[[ -z "$output" ]] && echo "nothing is going on" || echo "$output"
