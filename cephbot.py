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
except:
    print "config.yaml not found"
    exit()
try:
    SLACK_BOT_TOKEN = config['SLACK_BOT_TOKEN']
except:
    print "SLACK_BOT_TOKEN is not defined in config.yaml. This is needed to open a connection to the Slack API."
    exit()
try:
    SLACK_BOT_ID = config['SLACK_BOT_ID']
except:
    print "SLACK_BOT_ID is not defined in config.yaml. This is needed to know when cephbot should listen."
    exit()
try:
    SLACK_USER_IDS = config['SLACK_USER_IDS']
except:
    SLACK_USER_IDS = None
if not SLACK_USER_IDS:
    print "Any user can talk to me. SLACK_USER_IDS is not defined or is empty in config.yaml."
try:
    SLACK_CHANNEL_IDS = config['SLACK_CHANNEL_IDS']
except:
    SLACK_CHANNEL_IDS = None
if not SLACK_CHANNEL_IDS:
    print "I will respond in any channel. SLACK_CHANNEL_IDS is not defined or is empty in config.yaml."
try:
    SLACK_USER_ACCESS_DENIED = config['SLACK_USER_ACCESS_DENIED']
except:
    SLACK_USER_ACCESS_DENIED = "You do not have permission to use me."
try:
    SLACK_CHANNEL_ACCESS_DENIED = config['SLACK_CHANNEL_ACCESS_DENIED']
except:
    SLACK_CHANNEL_ACCESS_DENIED = "This channel does not have permission to use me."

try:
    CEPH_CLUSTER_ID = config['CEPH_CLUSTER_ID']
except:
    CEPH_CLUSTER_ID = "ceph"
try:
    CEPH_CONF = config['CEPH_CONF']
except:
    CEPH_CONF =  "/etc/ceph/ceph.conf"
try:
    CEPH_USER = config['CEPH_USER']
except:
    CEPH_USER = "client.admin"
try:
    CEPH_KEYRING = config['CEPH_KEYRING']
except:
    CEPH_KEYRING = "/etc/ceph/ceph.client.admin.keyring"

try:
    HELP_MSG = CEPH_CLUSTER_ID + ": " + config['HELP_MSG']
except:
    HELP_MSG = CEPH_CLUSTER_ID + ": status, osd stat, mon, stat, pg stat"
try:
    TOO_LONG = config["TOO_LONG"]
except:
    TOO_LONG = 20
try:
    TOO_LONG_MSG = config["TOO_LONG_MSG"]
except:
    TOO_LONG_MSG = "Response was too long. Check your DMs."


HELP = "help"
AT_BOT = "<@" + SLACK_BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

def ceph_command(command):
    cluster = rados.Rados(conffile=CEPH_CONF, conf=dict(keyring = CEPH_KEYRING), name=CEPH_USER)
    try:
        cluster.connect()
    except:
        print "Something prevented the connection to the Ceph cluster. Check your CEPH_USER and CEPH_KEYRING settings."
        exit()
    if command == "down osds" or command == "down osd":
        cmd = {"prefix":"osd tree", "format":"json"}
    else:
        cmd = {"prefix":command, "format":"plain"}
    try:
        ret, output, errs = cluster.mon_command(json.dumps(cmd), b'', timeout=5)
    except:
        return "Something went wrong while executing " + command + " on the Ceph cluster.", None
    cluster.shutdown()

    if command == "down osds" or command == "down osd":
        output = json.loads(output)
        lastroot = None
        lasthost = None
        msg = ""
        for item in output['nodes']:
            if item['type'] == 'root':
                root = item['name']
            elif item['type'] == 'host':
                host = item['name']
            elif item['type'] == 'osd' and item['status'] == 'down':
                osd = item['name']
                if not root == lastroot:
                    msg = msg + "\n" + root
                if not host == lasthost:
                    msg = msg + "\n    " + host
                msg = msg + "\n        " + osd
                lastroot = root
                lasthost = host
        output = msg.strip()
        if output == "":
            output = "All OSDs are up."

    if output and len(output.split('\n')) < TOO_LONG:
        return output, None
    elif output and len(output.split('\n')) >= TOO_LONG:
        return TOO_LONG_MSG, output
    else:
        return "Something went wrong while executing '" + command + "' on the Ceph cluster.", None


def handle_command(command, channel, user):
    if SLACK_USER_IDS and not user in SLACK_USER_IDS:
        channel_response = None
        user_response = SLACK_USER_ACCESS_DENIED
    else:
        command = command.strip().lower()
        if command.startswith(CEPH_CLUSTER_ID):
            command = command.split(CEPH_CLUSTER_ID)[1].strip().lower()
            if SLACK_CHANNEL_IDS and not channel.startswith('D') and not channel in SLACK_CHANNEL_IDS:
                channel_response = SLACK_CHANNEL_ACCESS_DENIED
                user_response = None
            elif command.startswith(HELP):
                channel_response = HELP_MSG
                user_response = None
            else:
                channel_response, user_response = ceph_command(command)
        elif command.startswith(HELP):
            if SLACK_CHANNEL_IDS and not channel.startswith('D') and not channel in SLACK_CHANNEL_IDS:
                channel_response = None
                user_response = None
            else:
                channel_response = HELP_MSG
                user_response = None
        else:
            return

    # Direct Messages have a channel that starts with a 'D'
    if channel_response and not ( channel_response and channel.startswith('D') and channel_response == TOO_LONG_MSG ):
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
            elif output and 'text' in output and output['channel'].startswith('D') and output['user'] != SLACK_BOT_ID:
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
