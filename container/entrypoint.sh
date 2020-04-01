#!/bin/bash

if [ -n "$(command -v yum)" ]; then
  yum -y install python-pip
elif [ -n "$(command -v apt-get)" ]; then
  apt-get -y install python-pip
fi

python2 -m pip install -r /cephbot/requirements.txt
/cephbot/cephbot.py
