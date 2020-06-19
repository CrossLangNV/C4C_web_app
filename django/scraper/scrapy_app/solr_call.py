import os

import pysolr


def solr_add(core="", docs=[]):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    client.add(docs, commit=True)


if __name__ == '__main__':
    os.environ['SOLR_URL'] = 'http://localhost:8983/solr'
