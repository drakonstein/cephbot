#!/usr/bin/python3

import os
import time
from slackclient import SlackClient
import rados
import json
import subprocess

# read config variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
if SLACK_BOT_TOKEN == '':
  print("SLACK_BOT_TOKEN is not defined. This is needed to open a connection to the Slack API.")
  exit()

SLACK_BOT_ID = os.getenv('SLACK_BOT_ID', '')
if SLACK_BOT_ID == '':
  print("SLACK_BOT_ID is not defined. This is needed to know when cephbot should listen.")
  exit()

SLACK_USER_IDS = os.getenv('SLACK_USER_IDS', None)
if not SLACK_USER_IDS:
  print("Any user can talk to me. SLACK_USER_IDS is not defined or is empty.")

SLACK_CHANNEL_IDS = os.getenv('SLACK_CHANNEL_IDS', None)
if not SLACK_CHANNEL_IDS:
  print("I will respond in any channel. SLACK_CHANNEL_IDS is not defined or is empty.")

SLACK_USER_ACCESS_DENIED = os.getenv('SLACK_USER_ACCESS_DENIED', "You do not have permission to use me.")
SLACK_CHANNEL_ACCESS_DENIED = os.getenv('SLACK_CHANNEL_ACCESS_DENIED', "This channel does not have permission to use me.")

CEPH_CLUSTER_ID = os.getenv('CEPH_CLUSTER_ID', "ceph").strip().lower()
CLUSTER_ALIASES = [i.lower() for i in os.getenv('CLUSTER_ALIASES', "all").strip().split()]

SCRIPTS_FOLDER = os.getenv('SCRIPTS_FOLDER', './scripts')

CEPH_CONF = os.getenv('CEPH_CONF', "/etc/ceph/ceph.conf")
CEPH_USER = os.getenv('CEPH_USER', "client.admin")
CEPH_KEYRING = os.getenv('CEPH_KEYRING', "/etc/ceph/ceph.client.admin.keyring")

HELP_MSG = CEPH_CLUSTER_ID + ": " + os.getenv('HELP_MSG', "status, osd stat, mon, stat, pg stat, down osds, blocked requests").strip()
TOO_LONG = os.getenv("TOO_LONG", 20)
TOO_LONG_MSG = "Long responses get threaded."

HELP = "help"
AT_BOT = "<@" + SLACK_BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

def ceph_command(command, thread):
  cluster = rados.Rados(conffile=CEPH_CONF, conf=dict(keyring = CEPH_KEYRING), name=CEPH_USER)
  run_mon_command = True
  try:
    cluster.connect()
  except:
    print("Something prevented the connection to the Ceph cluster. Check your CEPH_USER and CEPH_KEYRING settings.")
    exit()

  if command == "blocked requests":
    run_mon_command = False
    try:
      output = subprocess.check_output(['/usr/bin/timeout', '5', SCRIPTS_FOLDER + '/blocked_requests.sh', '--conf', CEPH_CONF, '--user', CEPH_USER, '--keyring', CEPH_KEYRING])
    except:
      return "Something went wrong while executing " + command + " on the Ceph cluster.", None
  elif command == "down osds" or command == "down osd":
    cmd = {"prefix":"osd tree", "format":"json"}
  elif command == "io":
    run_mon_command = False
    try:
      output = subprocess.check_output(['/usr/bin/timeout', '5', SCRIPTS_FOLDER + '/io.sh', '--conf', CEPH_CONF, '--user', CEPH_USER, '--keyring', CEPH_KEYRING])
    except:
      return "Something went wrong while executing " + command + " on the Ceph cluster.", None
  elif command.startswith("pool io"):
    opt_pool = command.split("pool io")[1].strip().lower()
    run_mon_command = False
    if opt_pool == None:
      try:
        output = subprocess.check_output(['/usr/bin/timeout', '5', SCRIPTS_FOLDER + '/pool_io.sh', '--conf', CEPH_CONF, '--user', CEPH_USER, '--keyring', CEPH_KEYRING])
      except:
        return "Something went wrong while executing " + command + " on the Ceph cluster.", None
    else:
      try:
        output = subprocess.check_output(['/usr/bin/timeout', '5', SCRIPTS_FOLDER + '/pool_io.sh', '--conf', CEPH_CONF, '--user', CEPH_USER, '--keyring', CEPH_KEYRING, '--pool', opt_pool])
      except:
        return "Something went wrong while executing " + command + " on the Ceph cluster.", None
  else:
    cmd = {"prefix":command, "format":"plain"}
  if run_mon_command:
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
          msg = msg + "\n" + root + "\n  " + host + "\n    " + osd
        elif not host == lasthost:
          msg = msg + "\n  " + host + "\n    " + osd
        else:
          msg = msg + ", " + osd
        lastroot = root
        lasthost = host
    output = msg.strip()
    if output == "":
      output = "All OSDs are up."

  output = output.strip()
  if output and ( len(output.splitlines()) < int(TOO_LONG) or thread ):
    return output, None
  elif output and len(output.splitlines()) >= int(TOO_LONG):
    return TOO_LONG_MSG, output
  else:
    return "Something went wrong while executing '" + command + "' on the Ceph cluster.", None


def handle_command(command, channel, user, thread):
  show_cluster_id = False
  command = command.strip().lower()
  cluster = command.split()[0]
  cluster_match = False
  if cluster == CEPH_CLUSTER_ID:
    cluster_match = True
  elif cluster in CLUSTER_ALIASES:
    cluster_match = True
    show_cluster_id = True
  if cluster_match:
    command = command.split(cluster, 1)[1].strip().lower()
    if SLACK_USER_IDS and not user in SLACK_USER_IDS:
      channel_response = None
      user_response = SLACK_USER_ACCESS_DENIED
    elif SLACK_CHANNEL_IDS and not channel.startswith('D') and not channel in SLACK_CHANNEL_IDS:
      channel_response = SLACK_CHANNEL_ACCESS_DENIED
      user_response = None
    elif command.startswith(HELP):
      channel_response = HELP_MSG
      user_response = None
    else:
      channel_response, user_response = ceph_command(command, thread)
  elif command.startswith(HELP):
    if SLACK_CHANNEL_IDS and not channel.startswith('D') and not channel in SLACK_CHANNEL_IDS:
      channel_response = None
      user_response = None
    elif SLACK_USER_IDS and not user in SLACK_USER_IDS:
      channel_response = None
      user_response = None
    else:
      channel_response = HELP_MSG
      user_response = None
  else:
    return

  response = None
  # Direct Messages have a channel that starts with a 'D'
  if channel_response and not ( channel_response and channel.startswith('D') and channel_response == TOO_LONG_MSG ):
    if show_cluster_id:
      channel_response = CEPH_CLUSTER_ID + ": " + channel_response
    if thread:
      slack_client.api_call("chat.postMessage", channel=channel, thread_ts=thread, text=channel_response, as_user=True)
    else:
      response = slack_client.api_call("chat.postMessage", channel=channel, text=channel_response, as_user=True)

  
  if user_response:
    if channel_response and channel_response == TOO_LONG_MSG and response:
      thread = response['ts']
    else:
      thread = None
    if show_cluster_id:
      user_response = CEPH_CLUSTER_ID + ": " + user_response
    if thread:
      slack_client.api_call("chat.postMessage", channel=channel, thread_ts=thread, text=user_response, as_user=True)
    else:
      slack_client.api_call("chat.postMessage", channel=user, text=user_response, as_user=True)


def parse_slack_output(slack_rtm_output):
  output_list = slack_rtm_output
  if output_list and len(output_list) > 0:
    for output in output_list:
      if output and 'thread_ts' in output:
        thread = output['thread_ts']
      else:
        thread = None
      if output and 'text' in output and AT_BOT in output['text']:
        # return text after the @ mention, whitespace removed
        return output['text'].split(AT_BOT, 1)[1].strip().lower(), \
             output['channel'], output['user'], thread
      # Direct Messages have a channel that starts with a 'D'
      elif output and 'text' in output and output['channel'].startswith('D') and output['user'] != SLACK_BOT_ID:
        return output['text'], output['channel'], output['user'], thread
  return None, None, None, None


if __name__ == "__main__":
  READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
  if slack_client.rtm_connect():
    print("CephBot connected and running!")
    while True:
      command, channel, user, thread = parse_slack_output(slack_client.rtm_read())
      if command and channel and user:
        handle_command(command, channel, user, thread)
      time.sleep(READ_WEBSOCKET_DELAY)
  else:
    print("Connection failed. Invalid Slack token or bot ID?")
