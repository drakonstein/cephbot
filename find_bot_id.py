#!/usr/bin/python2

import os
from slackclient import SlackClient
import yaml

# read config variables
config = yaml.safe_load(open("config.yaml"))
SLACK_BOT_TOKEN = config['SLACK_BOT_TOKEN']
SLACK_BOT_NAME = config['SLACK_BOT_NAME']

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


if __name__ == "__main__":
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == SLACK_BOT_NAME:
                print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
    else:
        print("could not find bot user with the name " + SLACK_BOT_NAME)
