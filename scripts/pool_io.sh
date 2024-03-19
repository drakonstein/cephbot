#!/bin/bash
args=$(/bin/sh $(dirname $0)/common_args.sh $@)
if (( $? != 0 )); then
  echo "$args"
  exit
fi

echo "$@" | grep -Eq '(-p|--pool) [[:alnum:]]+' && pool=true || pool=false

output=$(ceph osd pool stats $args)

if ! $pool; then
  output=$(echo "$output" | grep 'pool\|op/s\|wr\|rd\|client\|recovery' | grep -B1 'op/s\|wr\|rd\|client\|recovery' | grep -v '^$\|^--$')
  if [[ -z "$output" ]]; then
    output="nothing is going on"
  fi
fi

echo "$output"
