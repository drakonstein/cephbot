#!/bin/bash
[[ ! -z "$1" ]] && conf="--conf $1" || conf=
[[ ! -z "$2" ]] && user="--name $2" || user=
[[ ! -z "$3" ]] && keyring="--keyring $3" || keyring=
if [[ -z "$4" ]]; then
  stats=$(ceph $conf $user $keyring osd pool stats | grep -B2 'io' | grep -v '^$')
  output=$(echo "$stats" | grep -B2 "MB\|GB" | grep -v '^--$')
  if [[ -z "$stats" ]]; then
    echo "nothing is going on"
  elif [[ -z "$output" ]]; then
    echo "not much is going on"
  else
    echo "$output"
  fi
else
  ceph $conf $user $keyring osd pool stats $4
fi
