#!/bin/bash

conf="$CEPH_CONF_FILE"
user="$CEPH_USER"
keyring="$CEPH_KEYRING_FILE"
args=
pool=
error=

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
    --pool|-p)
      variable=pool
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
        pool)
          pool="$i"
          variable=
        ;;
        *)
          error+="\nUnknown option $i"
        ;;
      esac
    ;;
  esac
done
if [[ -n "$variable" ]]; then
  error+="\nYou invoked, but did not supply the $variable."
fi

if [[ -n "$conf" ]]; then
  if ! ls $conf &>/dev/null; then
    error+="\nconf not found: $conf"
  fi
  args="--conf $conf"
fi
[[ -n "$user" ]] && args+=" --name $user"
if [[ -n "$keyring" ]]; then
  if ! ls $keyring &>/dev/null; then
    error+="\nkeyring not found: $keyring"
  fi
  args+=" --keyring $keyring"
fi

if [[ -n "$error" ]]; then
  echo "$error"
  exit 1
else
  echo "$args" $pool
fi
