#!/usr/bin/python2

import os
import time
from slackclient import SlackClient
import rados
import json
import yaml

# read config variables
config = yaml.safe_load(open("config.yaml"))
CEPH_CLUSTER_ID = config['CEPH_CLUSTER_ID']
CEPH_CONF = config['CEPH_CONF']
CEPH_USER = config['CEPH_USER']
CEPH_KEYRING = config['CEPH_KEYRING']
SLACK_BOT_TOKEN = config['SLACK_BOT_TOKEN']
SLACK_BOT_ID = config['SLACK_BOT_ID']
AT_BOT = "<@" + SLACK_BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

def ceph_command(command):
    cluster = rados.Rados(conffile=CEPH_CONF, conf=dict(keyring = CEPH_KEYRING), name=CEPH_USER)
    cluster.connect()
    cmd = {"prefix":command, "format":"plain"}
    try:
        ret, output, errs = cluster.mon_command(json.dumps(cmd), b'', timeout=5)
    except:
        return "Something went wrong while executing " + command + " on the Ceph cluster."
    cluster.shutdown()

    if output:
        return output
    else:
        return "Something went wrong while executing '" + command + "' on the Ceph cluster."


def handle_command(command, channel):
    if command.startswith(CEPH_CLUSTER_ID):
        response = ceph_command(command.split(CEPH_CLUSTER_ID)[1].strip().lower())
    else:
        response = "I don't know how to help you that."
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("CephBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
