#!/usr/bin/python2

import os
import time
from slackclient import SlackClient
import rados
import json
import yaml

# read config variables
try:
    config = yaml.safe_load(open("config.yaml"))
    CEPH_CLUSTER_ID = config['CEPH_CLUSTER_ID']
    CEPH_CONF = config['CEPH_CONF']
    CEPH_USER = config['CEPH_USER']
    CEPH_KEYRING = config['CEPH_KEYRING']
    SLACK_BOT_TOKEN = config['SLACK_BOT_TOKEN']
    SLACK_BOT_ID = config['SLACK_BOT_ID']
    HELP_MSG = config['HELP_MSG']
    TOO_LONG = config["TOO_LONG"]
    TOO_LONG_MSG = config["TOO_LONG_MSG"]
except:
    print "Values missing in the config file. Please compare it to the example."
    exit()

HELP = "help"
AT_BOT = "<@" + SLACK_BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

def ceph_command(command):
    cluster = rados.Rados(conffile=CEPH_CONF, conf=dict(keyring = CEPH_KEYRING), name=CEPH_USER)
    try:
        cluster.connect()
    except:
        print "Something prevented the connection to the Ceph cluster."
        exit()
    cmd = {"prefix":command, "format":"plain"}
    try:
        ret, output, errs = cluster.mon_command(json.dumps(cmd), b'', timeout=5)
    except:
        return "Something went wrong while executing " + command + " on the Ceph cluster.", None
    cluster.shutdown()

    if output and len(output.split('\n')) < TOO_LONG:
        return output, None
    elif output and len(output.split('\n')) >= TOO_LONG:
        return TOO_LONG_MSG, output
    else:
        return "Something went wrong while executing '" + command + "' on the Ceph cluster.", None


def handle_command(command, channel, user):
    if command.startswith(CEPH_CLUSTER_ID):
        command = command.split(CEPH_CLUSTER_ID)[1].strip().lower()
        if command.startswith(HELP):
            channel_response = HELP_MSG
            user_response = None
        else:
            channel_response, user_response = ceph_command(command)
    elif command.startswith(HELP):
        channel_response = HELP_MSG
        user_response = None
    else:
        return

    # Direct Messages have a channel that starts with a 'D'
    if not ( channel_response and channel.startswith('D') and channel_response == TOO_LONG_MSG ):
        slack_client.api_call("chat.postMessage", channel=channel,
                          text=channel_response, as_user=True)

    if user_response:
        slack_client.api_call("chat.postMessage", channel=user,
                          text=user_response, as_user=True)


def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], output['user']
            # Direct Messages have a channel that starts with a 'D'
            if output and 'text' in output and output['channel'].startswith('D') and output['user'] != SLACK_BOT_ID:
                return output['text'], output['channel'], output['user']
    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("CephBot connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
