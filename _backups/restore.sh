#!/bin/bash
set -e
if [ $# -ne 1 ]; then
        echo "`date`: ERROR: Please start this script with:"
        echo "`date`: ERROR: $0 <backup folder to restore>"
        exit 1;
fi

# Settings
BACKUP_FOLDER=$1
NAMESPACE="fisma-ctlg-manager-develop"
SOLR_HOSTNAME="https://solr.dev.dgfisma.crosslang.com"

# Copy solr snapshots
SOLR_PODNAME=`rancher kubectl get pods --namespace=$NAMESPACE |grep solr | awk '{print $1}'`

# Documents
SNAPSHOT=`ls -dt $BACKUP_FOLDER/solr/data/documents/data/snapshot.* |head -n 1`
rancher kubectl exec -it $SOLR_PODNAME --namespace=$NAMESPACE -- rm -R /tmp/documents
rancher kubectl exec -it $SOLR_PODNAME --namespace=$NAMESPACE -- mkdir /tmp/documents
rancher kubectl cp $SNAPSHOT $SOLR_NAME:/tmp/documents --namespace=$NAMESPACE

# Files
SNAPSHOT=`ls -dt $BACKUP_FOLDER/solr/data/files/data/snapshot.* |head -n 1`
rancher kubectl exec -it $SOLR_PODNAME --namespace=$NAMESPACE -- rm -R /tmp/files
rancher kubectl exec -it $SOLR_PODNAME --namespace=$NAMESPACE -- mkdir /tmp/files
rancher kubectl cp $SNAPSHOT $SOLR_NAME:/tmp/files --namespace=$NAMESPACE

# Tell solr to restore latest snapshot
curl -k --user crosslang:isthebest "$SOLR_HOSTNAME/solr/documents/replication?command=restore&location=/tmp/documents"
curl -k --user crosslang:isthebest "$SOLR_HOSTNAME/solr/files/replication?command=restore&location/tmp/files"
