#!/bin/bash
conf="$CEPH_CONF"
user="$CEPH_USER"
keyring="$CEPH_KEYRING"

for i in $@; do
  case i in
    -c|--conf)
      variable=conf
    ;;
    -u|--user|-n|--name)
      variable=user
    ;;
    -k|--keyring)
      variable=keyring
    ;;
    *)
      case $variable in
        conf)
          conf="$i"
          variable=
        ;;
        user)
          user="$i"
          variable=
        ;;
        keyring)
          keyring="$i"
          variable=
        ;;
        *)
          echo "Unknown option"
          exit 1
        ;;
      esac
    ;;
  esac
done

[[ -n "$conf" ]] && conf="--conf $conf" || conf=
[[ -n "$user" ]] && user="--name $user" || user=
[[ -n "$keyring" ]] && keyring="--keyring $keyring" || keyring=

output=$(ceph $conf $user $keyring status | grep -A5 io | grep -v io)
[[ -z "$output" ]] && echo "nothing is going on" || echo "$output"
