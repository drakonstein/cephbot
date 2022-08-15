#!/bin/bash
conf="$CEPH_CONF_FILE"
user="$CEPH_USER"
keyring="$CEPH_KEYRING_FILE"

for i in "$@"; do
  case "$i" in
    --conf|-c)
      variable=conf
    ;;
    --user|-u|--name|-n)
      variable=user
    ;;
    --keyring|-k)
      variable=keyring
    ;;
    *)
      case "$variable" in
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
if [[ -n "$variable" ]]; then
  echo "You invoked, but did not supply the $variable."
  exit 1
fi

[[ -n "$conf" ]] && conf="--conf $conf" || conf=
[[ -n "$user" ]] && user="--name $user" || user=
[[ -n "$keyring" ]] && keyring="--keyring $keyring" || keyring=

output=$(ceph $conf $user $keyring status | grep -A5 io | grep -v io)
[[ -z "$output" ]] && echo "nothing is going on" || echo "$output"
