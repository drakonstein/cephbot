#!/bin/bash
if [[ "$1" == "quiet" ]]; then
  quiet=true
else
  quiet=false
fi

if [ -n "$(command -v yum)" ]; then
  cmd="yum -y install python-pip"
elif [ -n "$(command -v apt-get)" ]; then
  cmd="apt-get -y install python-pip"
fi
cmd2="python2 -m pip --disable-pip-version-check install -r /cephbot/requirements.txt"
if $quiet; then
  $cmd > /dev/null 2>&1
  $cmd2 > /dev/null 2>&1
else
  $cmd
  $cmd2
fi

python2 /cephbot/cephbot.py
