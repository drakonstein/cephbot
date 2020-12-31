#!/usr/bin/python3

import os
from slackclient import SlackClient

# read config variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_NAME = os.getenv('SLACK_BOT_NAME')
slack_client = SlackClient(SLACK_BOT_TOKEN)

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
