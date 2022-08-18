#!/usr/bin/python3

import os
import re
from slack_sdk.rtm_v2 import RTMClient
from slack_sdk import WebClient
from flask import Flask, make_response
import rados
import json
import subprocess

# read config variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
if SLACK_BOT_TOKEN == '':
  print("SLACK_BOT_TOKEN is not defined. This is needed to open a connection to the Slack API.")
  exit()

SLACK_USER_TOKEN = os.getenv('SLACK_USER_TOKEN', None)

SLACK_BOT_ID = os.getenv('SLACK_BOT_ID', '').strip().lower()
if SLACK_BOT_ID == '':
  print("SLACK_BOT_ID is not defined. This is needed to know when cephbot should listen.")
  exit()

EVENTS_SLACK_IDS_ = os.getenv('EVENTS_SLACK_IDS', None)
if EVENTS_SLACK_IDS_:
  EVENTS_SLACK_IDS = EVENTS_SLACK_IDS_.strip().split()
EVENTS_SLACK_CHANNELS_ = os.getenv('EVENTS_SLACK_CHANNELS', None)
if EVENTS_SLACK_CHANNELS_:
  EVENTS_SLACK_CHANNELS = EVENTS_SLACK_CHANNELS_.strip().split()
if EVENTS_SLACK_CHANNELS_ and EVENTS_SLACK_IDS_:
  EVENTS_ENABLED = True
else:
  EVENTS_ENABLED = False
  print("Either EVENTS_SLACK_CHANNELS or EVENTS_SLACK_IDS not set. No information will be added to alerting messages.")

EVENTS_TRIGGER = os.getenv('EVENTS_TRIGGER', "FIRING").strip().lower()
EVENTS_COMMANDS = os.getenv('EVENTS_COMMANDS', "health, io, down osds, blocked requests").strip().lower().split(", ")

SLACK_USER_IDS = os.getenv('SLACK_USER_IDS', None)
if not SLACK_USER_IDS:
  print("Any user can talk to me. SLACK_USER_IDS is not defined or is empty.")

SLACK_CHANNEL_IDS = os.getenv('SLACK_CHANNEL_IDS', None)
if not SLACK_CHANNEL_IDS:
  print("I will respond in any channel. SLACK_CHANNEL_IDS is not defined or is empty.")

SLACK_USER_ACCESS_DENIED = os.getenv('SLACK_USER_ACCESS_DENIED', "You do not have permission to use me.")
SLACK_CHANNEL_ACCESS_DENIED = os.getenv('SLACK_CHANNEL_ACCESS_DENIED', "This channel does not have permission to use me.")

CEPH_CLUSTERS = {}
ceph_cluster_ids_regex = re.compile(r'^CEPH_CLUSTER_')
for key, value in os.environ.items():
  if ceph_cluster_ids_regex.search(key):
    cluster = value.strip().lower().split(":")
    CEPH_CLUSTERS[cluster[0].strip()] = cluster[1].strip()

SCRIPTS_FOLDER = os.getenv('SCRIPTS_FOLDER', './scripts')

CEPH_CONF = os.getenv('CEPH_CONF_FILE', "/etc/ceph/ceph.conf")
CEPH_USER = os.getenv('CEPH_USER', "client.admin")
CEPH_KEYRING = os.getenv('CEPH_KEYRING_FILE', "/etc/ceph/ceph.client.admin.keyring")

READINESS_FILE = os.getenv('READINESS_FILE', "~/ready.txt")
FLASK_PORT = os.getenv('FLASK_PORT', "8080")

HELP_MSG = ": " + os.getenv('HELP_MSG', "status, osd stat, mon, stat, pg stat, down osds, blocked requests").strip()
TOO_LONG = os.getenv("TOO_LONG", 20)
TOO_LONG_MSG = "Long responses get threaded."
ALWAYS_THREAD = os.getenv('ALWAYS_THREAD', 'false').lower() in ('true', '1', 't')
ALWAYS_SHOW_CLUSTER_ID = os.getenv('ALWAYS_SHOW_CLUSTER_ID', 'false').lower() in ('true', '1', 't')

HELP = "help"
AT_BOT = "<@" + SLACK_BOT_ID + ">"

rtm = RTMClient(token=SLACK_BOT_TOKEN)
webClient = WebClient(token=SLACK_USER_TOKEN)
flaskApp = Flask(__name__)

@flaskApp.route("/health", methods=["GET"])
def cephbot_health():
  if rtm is not None and rtm.is_connected():
    return make_response("OK", 200)
  return makeresponse("Cephbot is inactive", 503)


def ceph_command(CLUSTER, command, thread):
  ceph_conf = CEPH_CONF.replace("CLUSTER", CLUSTER)
  ceph_keyring = CEPH_KEYRING.replace("CLUSTER", CLUSTER).replace("CEPH_USER", CEPH_USER)

  cluster = rados.Rados(conffile=ceph_conf, conf=dict(keyring = ceph_keyring), name=CEPH_USER)
  run_mon_command = True
  try:
    cluster.connect()
  except:
    print("Something prevented the connection to the Ceph cluster. Attempted using the following settings.")
    print("CEPH_CONF: " + ceph_conf)
    print("CEPH_USER: " + CEPH_USER)
    print("CEPH_KEYRING: " + ceph_keyring)
    return "Something went wrong while connecting to " + CLUSTER + " using " + ceph_conf + ", " + CEPH_USER + ", " + ceph_keyring, None

  if command == "blocked requests":
    run_mon_command = False
    try:
      output = subprocess.check_output(['/usr/bin/timeout', '5', '/bin/sh', SCRIPTS_FOLDER + '/blocked_requests.sh', '--conf', ceph_conf, '--user', CEPH_USER, '--keyring', ceph_keyring])
    except:
      return "Something went wrong while executing " + command + " on the Ceph cluster.", None
  elif command == "down osds" or command == "down osd":
    cmd = {"prefix":"osd tree", "format":"json"}
  elif command == "io":
    run_mon_command = False
    try:
      output = subprocess.check_output(['/usr/bin/timeout', '5', '/bin/sh', SCRIPTS_FOLDER + '/io.sh', '--conf', ceph_conf, '--user', CEPH_USER, '--keyring', ceph_keyring])
    except:
      return "Something went wrong while executing " + command + " on the Ceph cluster.", None
  elif command.startswith("pool io"):
    opt_pool = command.split("pool io")[1].strip().lower()
    run_mon_command = False
    if opt_pool == None:
      try:
        output = subprocess.check_output(['/usr/bin/timeout', '5', '/bin/sh', SCRIPTS_FOLDER + '/pool_io.sh', '--conf', ceph_conf, '--user', CEPH_USER, '--keyring', ceph_keyring])
      except:
        return "Something went wrong while executing " + command + " on the Ceph cluster.", None
    else:
      try:
        output = subprocess.check_output(['/usr/bin/timeout', '5', '/bin/sh', SCRIPTS_FOLDER + '/pool_io.sh', '--conf', ceph_conf, '--user', CEPH_USER, '--keyring', ceph_keyring, '--pool', opt_pool])
      except:
        return "Something went wrong while executing " + command + " on the Ceph cluster.", None
  elif command.startswith("health detail"):
    run_mon_command = False
    try:
      output = subprocess.check_output(['/usr/bin/timeout', '5', '/bin/sh', SCRIPTS_FOLDER + '/health_detail.sh', '--conf', ceph_conf, '--user', CEPH_USER, '--keyring', ceph_keyring])
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

  output = output.decode('utf-8').strip()

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
    return "Something went wrong while executing '" + command + "' on " + CLUSTER + ".", None


@rtm.on("message")
def slack_parse(client: RTMClient, event: dict):
  for_cephbot = False
  events_run = False
  cluster_match = False
  clusters_matched = []
  check_thread = False

  if 'thread_ts' in event:
    thread = event['thread_ts']
    check_thread = True
  elif ALWAYS_THREAD:
    thread = event['ts']
  else:
    thread = None
  show_cluster_id = ALWAYS_SHOW_CLUSTER_ID

  if 'text' in event:
    command = event['text'].strip().lower()
    channel = event['channel']
    user = event['user']

    if user == SLACK_BOT_ID:
      return
    elif EVENTS_ENABLED and user in EVENTS_SLACK_IDS and channel in EVENTS_SLACK_CHANNELS and EVENTS_TRIGGER in command:
      for CLUSTER in CEPH_CLUSTERS:
        if CLUSTER in command:
          for_cephbot = True
          events_run = True
          cluster_match = True
          clusters_matched.append(CLUSTER)
          if thread == None:
            thread = event['ts']
    elif AT_BOT in command:
      for_cephbot = True
      command = command.split(AT_BOT, 1)[1].strip()
    elif channel.startswith('D'):
      for_cephbot = True
    elif check_thread && SLACK_USER_TOKEN is not None:
      messages = webClient.conversations_replies(channel=channel, inclusive=True, ts=thread)
      for message in messages.data['messages']:
        if message['user'].lower() == SLACK_BOT_ID:
          for_cephbot = True
          break
        elif AT_BOT in message['text'].lower():
          for_cephbot = True
          break

  if not for_cephbot:
    return

  if not events_run:
    cluster = command.split()[0]
    if command.startswith(HELP):
      clusters_matched = CEPH_CLUSTERS
    for CLUSTER in CEPH_CLUSTERS:
      if cluster == CLUSTER:
        cluster_match = True
        clusters_matched.append(CLUSTER)
      else:
        for ALIAS in CEPH_CLUSTERS[CLUSTER].split():
          if cluster == ALIAS.strip():
            cluster_match = True
            clusters_matched.append(CLUSTER)
            show_cluster_id = True
            break
    if cluster_match:
      command = command.split(cluster, 1)[1].strip().lower()

  commands = []
  if events_run:
    commands = EVENTS_COMMANDS
  else:
    commands.append(command)

  for CLUSTER in clusters_matched:
    for command in commands:
      channel_response = None
      user_response = None
      if SLACK_USER_IDS and not user in SLACK_USER_IDS:
        channel_response = None
        user_response = SLACK_USER_ACCESS_DENIED
      elif SLACK_CHANNEL_IDS and not channel.startswith('D') and not channel in SLACK_CHANNEL_IDS:
        channel_response = SLACK_CHANNEL_ACCESS_DENIED
        user_response = None
      elif command.startswith(HELP):
        help_msg = HELP_MSG
        if "ALIASES" in help_msg:
          help_msg = help_msg.replace("ALIASES", CEPH_CLUSTERS[CLUSTER])
        channel_response = CLUSTER + help_msg
        user_response = None
      else:
        channel_response, user_response = ceph_command(CLUSTER, command, thread)
      response = None

      # Direct Messages have a channel that starts with a 'D'
      if channel_response and not ( channel_response and channel.startswith('D') and channel_response == TOO_LONG_MSG ):
        if show_cluster_id:
          if not channel_response.startswith(CLUSTER):
            channel_response = CLUSTER + ": " + channel_response
        if thread:
          client.web_client.chat_postMessage(
            channel=channel,
            thread_ts=thread,
            text=channel_response,
            as_user=True
          )
        else:
          response = client.web_client.chat_postMessage(channel=channel, text=channel_response, as_user=True)

      if user_response:
        if channel_response and channel_response == TOO_LONG_MSG and response:
          thread = response['ts']
        else:
          thread = None
        if show_cluster_id:
          if not channel_response.startswith(CLUSTER):
            user_response = CLUSTER + ": " + user_response
        if thread:
          client.web_client.chat_postMessage(
            channel=channel,
            thread_ts=thread,
            text=user_response,
            as_user=True
          )
        else:
          client.web_client.chat_postMessage(
            channel=user,
            text=user_response,
            as_user=True
          )

if __name__ == "__main__":
  try:
    rtm.connect()
  except:
    print("Connection failed. Invalid Slack token or bot ID?")
    exit()

  if rtm.is_connected():
    f = open(READINESS_FILE, "w")
    f.write("Slack connection made")
    f.close()
    flaskApp.run(port=FLASK_PORT)
  else:
    print("Connection failed or disconnected.")
    exit()

  print("Good-Bye")
