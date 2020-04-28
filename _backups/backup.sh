#/bin/bash
set -e

# Tell solr to create restore latest snapshot
curl -k --user crosslang:isthebest "https://solr.dgfisma.crosslang.com/solr/documents/replication?command=backup&numberToKeep=1"
curl -k --user crosslang:isthebest "https://solr.dgfisma.crosslang.com/solr/files/replication?command=backup&numberToKeep=1"

#sleep 60

NAMESPACE="fisma-ctlg-manager"
POSTGRESQL_PODNAME=`rancher kubectl get pods --namespace=$NAMESPACE |grep postgres | awk '{print $1}'`
SOLR_PODNAME=`rancher kubectl get pods --namespace=$NAMESPACE |grep solr | awk '{print $1}'`
SCRAPY_PODNAME=`rancher kubectl get pods --namespace=$NAMESPACE |grep scrapy | awk '{print $1}'`

BACKUP_FOLDER=`date +%Y-%m-%d"_"%H_%M_%S`
echo $POSTGRESQL_PODNAME
echo $SOLR_PODNAME

mkdir -p $BACKUP_FOLDER
cd $BACKUP_FOLDER
rancher kubectl exec -it $POSTGRESQL_PODNAME --namespace=$NAMESPACE -- pg_dumpall -c -U django > dump.sql
rancher kubectl cp $NAMESPACE/$SOLR_PODNAME:/var/solr solr
rancher kubectl cp $NAMESPACE/$SCRAPY_PODNAME:/scrapy scrapy
cd ..
