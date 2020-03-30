## Django - Solr app

Django search web application with PostgreSQL as the db backend for Django (administration) and with Solr as the main db / search engine.

Provide a `secrets/django-docker.env` and run with `docker-compose up -d` (see secrets/django-docker.env.sample)

Data for both PostgreSQL and Solr is persisted through named volumes.


### Django data

First enter django docker:

`docker exec -it ctlg-manager_django_1 /bin/bash`

You can create a admin user with these commands:

`python manage.py createsuperuser --username $DJANGO_ADMIN_USERNAME --email $DJANGO_ADMIN_EMAIL`

The angular app required an applicaiton (uses django-oath-toolkit):

`python manage.py createapplication --client-id $ANGULAR_DJANGO_CLIENT_ID --client-secret $ANGULAR_DJANGO_CLIENT_SECRET --name searchapp confidential password`

### Solr data

The Solr service is started by docker-compose and will create a core named `films` if it doesn't exist yet.

Load the example films data (following https://lucene.apache.org/solr/guide/8_4/solr-tutorial.html):

1. Create the "name" field
2. Create the "catchall" copy field
3. Index sample film data
```
bin/post -c films example/films/films.json
```

### Django app

Open browser at `http://localhost:8000`
