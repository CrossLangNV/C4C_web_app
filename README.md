<table cellspacing="0" cellpadding="0">
    <tr>
        <td><img src="https://user-images.githubusercontent.com/8747446/160939167-1e70640f-ba7d-48fa-93a3-7167520fbbd7.png" width="300"></td>
        <td><img src="https://user-images.githubusercontent.com/8747446/160938749-10b34fed-c9e8-4644-8218-2d61fcae5299.png" width="400"></td>
    </tr>
</table>

# C4C Web App

## UIMA

Because the UIMA source code is in a separate Git submodule, execute the following command:
`git submodule update --init`

After the code is available, the UIMA project must be built with Maven:

`mvn clean install`

## Django - Solr app

Django search web application with PostgreSQL as the db backend for Django (administration) and with Solr as the main db / search engine.

Provide a `secrets/django-docker.env` and run with `docker-compose up -d` (see secrets/django-docker.env.sample)

Data for both PostgreSQL and Solr is persisted through named volumes.

Create solr collection:

`docker-compose exec solr bin/solr create -c archive`

Configure Solr to have all the fields, run the following command in the solr directory:

`./fields.sh`

### Django data

First enter django docker:

`docker-compose exec django /bin/bash`

You can create a admin user with these commands:

`python manage.py createsuperuser --username $DJANGO_ADMIN_USERNAME --email $DJANGO_ADMIN_EMAIL`

The angular app requires an application (uses django-oath-toolkit):

`python manage.py createapplication --name searchapp confidential password`

In your browser, navigate to `http://localhost:8000/admin/oauth2_provider/application/`
Go to the detail page of the searchapp app by clicking on it's id in the list of applications.
In the user field, add the admin user.

### Solr data

The Solr service is started by docker-compose and will create a core named `documents` if it doesn't exist yet.

### Django app

Open browser at `http://localhost:8000`

### Django Unit Tests

Put your unit test in a file that matches "test\*py"

To run tests from module scheduler:

`docker-compose exec django python manage.py test scheduler`

### Scrapy app

During development you can run the scrapy spiders by opening a django shell

`docker-compose exec django /bin/bash`

Then:

`scrapy crawl -s CLOSESPIDER_ITEMCOUNT=5 -a year=1953 -L DEBUG eurlex`

Or:

`scrapy crawl -a spider_date_start=01011953 -a spider_date_end=01011960 eurlex`

### Rancher

Some helpfull commands

Look up pod name:

`rancher kubectl get pods --namespace=fisma-ctlg-manager`

Open postgresql shell:

`rancher kubectl exec -it postgres-5b5bbf9f65-5c8mv --namespace=fisma-ctlg-manager -- psql --username django`

### Backup

Postgres:

rancher kubectl exec -it postgres-5b5bbf9f65-5c8mv --namespace=fisma-ctlg-manager -- pg*dumpall -c -U django > dump*`date +%d-%m-%Y"_"%H_%M_%S`.sql

Solr:

curl -k -v --user crosslang:<pass> "https://solr.dgfisma.crosslang.com/solr/documents/replication?command=backup"
curl -k -v --user crosslang:<pass> "https://solr.dgfisma.crosslang.com/solr/files/replication?command=backup"

rancher kubectl cp fisma-ctlg-manager/solr-df687b79b-hrnmj:/var/solr solr-df687b79b-hrnmj

### How to get data in your local environment (updated 22/9/2020)

- Go to http://localhost:8000/admin/searchapp/website/
- Add the following websites for example `EURLEX` `SRB`
- Select the websites and run each action seperately from `Scrape website` to `Extract terms`
- After a few minutes of scraping with `Scrape website`, restart your celery container because this could take a lot of time
