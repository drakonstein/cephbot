#!/bin/bash

if [ -n "$(command -v yum)" ]; then
  yum -y install python-pip 2>&1 > /dev/null
elif [ -n "$(command -v apt-get)" ]; then
  apt-get -y install python-pip 2>&1 > /dev/null
fi

python2 -m pip install -r /cephbot/requirements.txt 2>&1 > /dev/null
python2 /cephbot/cephbot.py
