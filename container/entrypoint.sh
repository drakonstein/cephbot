#!/bin/bash
if [[ "$1" == "quiet" ]]; then
  quiet="2>&1 > /dev/null"
else
  quiet=
fi

if [ -n "$(command -v yum)" ]; then
  yum -y install python-pip $quiet
elif [ -n "$(command -v apt-get)" ]; then
  apt-get -y install python-pip $quiet
fi

python2 -m pip --disable-pip-version-check install -r /cephbot/requirements.txt $quiet
python2 /cephbot/cephbot.py
