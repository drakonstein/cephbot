#!/bin/bash
[[ ! -z "$1" ]] && conf="--conf $1" || conf=
[[ ! -z "$2" ]] && user="--name $2" || user=
[[ ! -z "$3" ]] && keyring="--keyring $3" || keyring=
output=$(ceph $conf $user $keyring status | grep -A5 io | grep -v io)
[[ -z "$output" ]] && echo "nothing is going on" || echo "$output"
