#!/bin/bash
args=$(/bin/sh $(dirname $0)/common_args.sh $@)
if (( $? != 0 )); then
  echo "$args"
  exit
fi

NONE="No RGWs running"

output=$(ceph $args status -f json | \
  jq -r '.servicemap.services.rgw.daemons |
    to_entries[] |
    select(.key != "summary") |
    .value.metadata |
    "\(.hostname) \(.ceph_version_short) \(.realm_name)/\(.zonegroup_name)/\(.zone_name)"' 2>/dev/null \
  || echo "$NONE")

if [[ -z "$output" ]]; then
  echo "Something went wrong attempting to retrieve the RGW information."
elif [[ "$output" == "$NONE" ]]; then
  echo "$output"
else
  output=$(echo "$output" | sort | uniq -c | awk '{ n = $1; $1=$2; $2= n; print }')
  echo "hostname # version realm/zonegroup/zone
  $output" | column -t
fi
