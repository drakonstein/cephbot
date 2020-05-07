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
    -p|--pool)
      variable=pool
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
        pool)
          pool="$i"
          variable=
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

if [[ -n "$pool" ]]; then
  ceph $conf $user $keyring osd pool stats $pool
else
  stats=$(ceph $conf $user $keyring osd pool stats | grep 'pool\|op/s\|wr\|rd\|client\|recovery' | grep -B1 'op/s\|wr\|rd\|client\|recovery' | grep -v '^$\|^--$')
  if [[ -z "$stats" ]]; then
    echo "nothing is going on"
  else
    echo "$stats"
  fi
fi
