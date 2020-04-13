## Django - Solr app

Django search web application with PostgreSQL as the db backend for Django (administration) and with Solr as the main db / search engine.

Provide a `secrets/django-docker.env` and run with `docker-compose up -d` (see secrets/django-docker.env.sample)

Data for both PostgreSQL and Solr is persisted through named volumes.


### Django data

First enter django docker:

`docker exec -it ctlg-manager_django_1 /bin/bash`

You can create a admin user with these commands:

`python manage.py createsuperuser --username $DJANGO_ADMIN_USERNAME --email $DJANGO_ADMIN_EMAIL`

The angular app requires an application (uses django-oath-toolkit):

`python manage.py createapplication --client-id $ANGULAR_DJANGO_CLIENT_ID --client-secret $ANGULAR_DJANGO_CLIENT_SECRET --name searchapp confidential password`

### Solr data

The Solr service is started by docker-compose and will create a core named `documents` if it doesn't exist yet.

An additional core should be created

`docker exec ctlg-manager_solr_1 solr create -c files -d /opt/solr/server/solr/configsets/myconfig -n myconfig`
`rancher kubectl exec solr-df687b79b-hrnmj  --namespace=fisma-ctlg-manager -- solr create -c files -d /opt/solr/server/solr/configsets/myconfig -n myconfig`


### Django app

Open browser at `http://localhost:8000`


### Rancher

Some helpfull commands

Look up pod name:

`rancher kubectl get pods --namespace=fisma-ctlg-manager`

Open postgresql shell:

`rancher kubectl exec -it postgres-5b5bbf9f65-5c8mv --namespace=fisma-ctlg-manager -- psql --username django`

Backup:

rancher kubectl exec -it postgres-5b5bbf9f65-5c8mv --namespace=fisma-ctlg-manager -- pg_dumpall -c -U django > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql
