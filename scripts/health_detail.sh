#!/bin/bash
conf="$CEPH_CONF"
user="$CEPH_USER"
keyring="$CEPH_KEYRING"

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

ceph $conf $user $keyring health detail
