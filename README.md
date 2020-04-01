# cephbot
Slack bot for Ceph

I got my start for interfacing with slack from here. Thank you Matt Makai. https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

The setup for this is pretty simple.  You need to find the Slack Bot's Token, Name, and ID.  There is an example script to get the Bot's ID.  The Token and Name will be visible in the Bot name on Slack's website for it.

I generally create a client.cephbot user in Ceph for this `ceph auth get-or-create client.cephbot mon 'allow r' mgr 'allow r' > /etc/ceph/ceph.client.cephbot.keyring` which prevents people in Slack for figuring out ways of performing operations against the cluster.  If you do enable cephbot to perform maintenance on the cluster, I highly recommend that you utilize the SLACK_USER_IDS and SLACK_CHANNEL_IDS config options to limit who can interface with cephbot.

Required non-standard Python libraries are slackclient which can be installed via pip.

``` bash
pip install -r requirements.txt
```

The server this is running on needs to have ceph installed (for bash scripts in the scripts/ directory and the rados python library) and needs to be able to communicate with the mons, but otherwise does not require any other cluster integrations.

To run this for multiple clusters, spin up multiple instances of it with a different CEPH_CLUSTER_ID in the config as well as a different CEPH_CONF and CEPH_KEYRING for each additional cluster.  I like to do this in a screen with multiple windows on the screen from a server that can communicate with all of the ceph clusters (a master admin node), but running each on a different server for each cluster would work as well as long as the server can also communicate with Slack.

## Execution
Update the .env files with your values.  Then execute the following:

``` bash
source .env
python cephbot.py
```
