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

output=$(ceph $conf $user $keyring health detail | grep 'ops are blocked' | sort -nrk6 | sed 's/ ops/+ops/' | sed 's/ sec/+sec/' | column -t -s'+')
if [[ -z "$output" ]]; then
    echo "No blocked requests"
else
    echo "$output" | grep -v 'on osd'
    echo "$output" | grep -Eo osd.[0-9]+ | sort -n | uniq -c | grep -v ' 1 '
    echo "$output" | grep 'on osd'
fi
