## Django - Solr app

Django search web application with PostgreSQL as the db backend for Django (administration) and with Solr as the main db / search engine.

Provide a `secrets/django-docker.env` and run with `docker-compose up -d`.

Data for both PostgreSQL and Solr is persisted through named volumes.

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