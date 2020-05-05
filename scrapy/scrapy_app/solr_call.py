import os

import pysolr


def solr_add(core="", docs=[]):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    client.add(docs, commit=True)


def solr_add_file(core, file, file_id, file_url, document_id):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    extra_params = {
        'commit': 'true',
        'literal.id': file_id,
        'resource.name': file.name,
        'literal.url': file_url,
        'literal.document_id': document_id
    }
    client.extract(file, extractOnly=False, **extra_params)


if __name__ == '__main__':
    os.environ['SOLR_URL'] = 'http://localhost:8983/solr'
