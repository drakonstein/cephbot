#!/bin/bash
args=$(/bin/sh $(dirname $0)/common_args.sh $@)
if (( $? != 0 )); then
  echo "$args"
  exit
fi

ceph $args health detail
