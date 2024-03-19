# cephbot
Containerized version of cephbot

I'm really excited to have this configured for kubernetes. It is so much nicer to not deal with this running in a screen. Thanks to @code4clouds for his help with this.

This includes the files needed to configure cephbot in k8s and uses the official Ceph container to simplify configuration.

If you're following the default examples in here you'll need to apply the various files like this.

``` bash
# If you haven't created your keyring yet, you can do so with something like this.
ceph auth get-or-create client.cephbot mon 'allow r' mgr 'allow r' > /etc/ceph/ceph.client.cephbot.keyring
kubectl create secret generic cephbot-conf --from-file=/path/to/ceph.conf --from-file=/path/to/keyring

# Create a secret for your Slack Bot's Token to make commiting these files into git safer.
kubectl create secret generic cephbot-token --from-literal=token='{{ SLACK_BOT_TOKEN }}'

# Edit your environment variables to match what you need and then create the deployment.
kubectl apply -f deployment.yaml
```
