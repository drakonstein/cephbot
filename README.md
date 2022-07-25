# cephbot
Slack bot for Ceph

There are instructions for how to deploy this to kubernetes in the kubernetes folder of this repo.

The setup for this is pretty simple. You need to find the Slack Bot's Token, Name, and ID. There is an example script to get the Bot's ID. The Token and Name will be visible in the Bot name on Slack's website for it.

I generally create a client.cephbot user in Ceph for this `ceph auth get-or-create client.cephbot mon 'allow r' mgr 'allow r' > /etc/ceph/ceph.client.cephbot.keyring` which prevents people in Slack for figuring out ways of performing operations against the cluster. If you do enable cephbot to perform maintenance on the cluster, I highly recommend that you utilize the SLACK_USER_IDS and SLACK_CHANNEL_IDS config options to limit who can interface with cephbot.

Required non-standard Python libraries are slack_sdk which can be installed via pip.

``` bash
pip install -r requirements.txt
```

The server this is running on needs to have ceph installed (for bash scripts in the scripts/ directory and the rados python library) and needs to be able to communicate with the mons, but otherwise does not require any other cluster integrations.

Cephbot is now capable of communicating with multiple clusters in one instance. It will iterate through all environment variables that start with "CEPH_CLUSTER_". The value of the variables should be in the format "cluster: alias1 alias2 alias3". For CEPH_CONF and CEPH_KEYRING you can use CLUSTER as a literal string in the variable that will be replaced by the cluster name specified in CEPH_CLUSTER variables. If you are not running this in kubernetes, I would run it in a screen with the environment variables set up. Each instance can be configured for 1 or all of your clusters.

## Execution
Update the .env files with your values. Then execute the following:

``` bash
source .env
python cephbot.py
```
