#!/bin/bash
if [[ "$1" == "quiet" ]]; then
  quiet=true
else
  quiet=false
fi

if python3 -m pip --version; then
  cmd="echo pip already installed"
else
  if [[ -n "$(command -v yum)" ]]; then
    cmd="yum -y install python3-pip"
  elif [[ -n "$(command -v apt-get)" ]]; then
    cmd="apt-get -y install python3-pip"
  fi
fi

cmd2="python3 -m pip --disable-pip-version-check install -r /cephbot/requirements.txt"
if $quiet; then
  echo "Output of the following commands has been suppressed."
  echo "$cmd"
  $cmd > /dev/null 2>&1
  echo "done"
  echo "$cmd2"
  $cmd2 > /dev/null 2>&1
  echo "done"
else
  $cmd
  $cmd2
fi

python3 /cephbot/cephbot.py
