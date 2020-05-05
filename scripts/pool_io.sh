#!/bin/bash
[[ ! -z "$1" ]] && conf="--conf $1" || conf=
[[ ! -z "$2" ]] && user="--name $2" || user=
[[ ! -z "$3" ]] && keyring="--keyring $3" || keyring=
if [[ -z "$4" ]]; then
  stats=$(ceph $conf $user $keyring osd pool stats | grep 'pool\|op/s\|wr\|rd\|client\|recovery' | grep -B1 'op/s\|wr\|rd\|client\|recovery' | grep -v '^$\|^--$')
  if [[ -z "$stats" ]]; then
    echo "nothing is going on"
  else
    echo "$stats"
  fi
else
  ceph $conf $user $keyring osd pool stats $4
fi
