# cephbot
Slack bot for Ceph

There are instructions for how to deploy this to kubernetes in the kubernetes folder of this repo.

The setup for this is pretty simple. You need to find the Slack Bot's Token and ID.

I generally create a client.cephbot user in Ceph for this `ceph auth get-or-create client.cephbot mon 'allow r' mgr 'allow r' > /etc/ceph/ceph.client.cephbot.keyring` which prevents people in Slack for figuring out ways of performing operations against the cluster. If you do enable cephbot to perform maintenance on the cluster, I highly recommend that you utilize the SLACK_USER_IDS and SLACK_CHANNEL_IDS config options to limit who can interface with cephbot.

Required non-standard Python libraries are slack_bolt and flask which can be installed via pip.

``` bash
pip install -r requirements.txt
```

The server this is running on needs to have ceph installed (for bash scripts in the scripts/ directory and the rados python library) and needs to be able to communicate with the mons, but otherwise does not require any other cluster integrations.

## Environment Variables
Including default values
### Required
For use with the RTM API (required when running multiple instances of cephbot so that Slack will make all messages available to all endpoints)
```SLACK_BOT_TOKEN=
SLACK_BOT_ID=
```

### Limit access to cephbot
This is only really useful if your keyring can perform administrative tasks.
``` bash
SLACK_USER_ACCESS_DENIED="You do not have permission to use me."
SLACK_USER_IDS=
SLACK_CHANNEL_ACCESS_DENIED="This channel does not have permission to use me."
SLACK_CHANNEL_IDS=
```

### Events
Using the EVENTS_* variables you can configure cephbot to monitor channels where zabbix, alertmanager, etc place notifications and it will parse messages in EVENTS_SLACK_CHANNELS from EVENTS_SLACK_IDS that include the EVENTS_TRIGGER for the cluster names and thread the EVENTS_COMMANDS in response to the event. This will give additional cluster information in slack in response to any events in the ceph cluster as the event triggers rather than later when engineers can sign in to investigate.
``` bash
EVENTS_SLACK_IDS=
EVENTS_SLACK_CHANNELS=
EVENTS_DEBUG=False
EVENTS_TRIGGER=FIRING
EVENTS_COMMANDS="health, io, down osds, blocked requests"
```

### Ceph configuration
For each ceph cluster you need to set up an environment variable with cluster name after "CEPH_CLUSTER_". The value of the variable are the aliases that the cluster will respond to. In this example the cluster's name is `ceph` and the alias is `all`.
``` bash
CEPH_CLUSTER_ceph="all"
```
Can use CLUSTER as a variable that will be replaced with the responding clusters name
``` bash
CEPH_CONF_FILE="/etc/ceph/CLUSTER.conf"
CEPH_USER="client.admin"
```
Can use CLUSTER and CEPH_USER as variables that will be replaced with responding clusters name and the above specified CEPH_USER variable
``` bash
CEPH_KEYRING_FILE="/etc/ceph/CLUSTER.CEPH_USER.keyring"
```

### Flask port
This port is used for health checks
``` bash
FLASK_PORT=8080
```

### Misc
``` bash
SCRIPTS_FOLDER="./scripts"
HELP_MSG="health, health detail, status, osd stat, mon stat, pg stat, down osds, blocked requests, rgw stat"
```
To keep down channel noise, messages longer than 20 lines will be threaded. To further keep down channel noise always thread responses regardless of length. Any time an alias is used, the responses will be threaded.
``` bash
TOO_LONG="20"
TOO_LONG_MSG = "Long responses get threaded."
ALWAYS_THREAD=False
```
When using aliases the reponding clusters will respond with their names. Sometimes its nice to just always have cephbot responses include the cluster name.
``` bash
ALWAYS_SHOW_CLUSTER_ID=False
```
Only report back if there is an unhealthy response from a cluster. Making it very easy to check overall health with large amounts of clusters.
``` bash
ERRORS_ONLY_STRS="ERRORS ERROR UNHEALTHY PROBLEMS PROBLEM"
```

## Multiple Clusters
Cephbot is now capable of communicating with multiple clusters in one instance. It will iterate through all environment variables that start with "CEPH_CLUSTER_". The value of the variables should be in the format "cluster: alias1 alias2 alias3". For CEPH_CONF and CEPH_KEYRING you can use CLUSTER as a literal string in the variable that will be replaced by the cluster name specified in CEPH_CLUSTER variables. If you are not running this in kubernetes, I would run it in a screen with the environment variables set up. Each instance can be configured for 1 or all of your clusters.

## Execution
Create an environment (ie .env) file with your values. Then execute the following:

``` bash
source .env
python cephbot.py
```
