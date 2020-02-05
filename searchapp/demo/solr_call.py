import pysolr
import os


def solr_search(core="", term=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search(term,
                                       **{'rows': 100, 'hl': 'on', 'hl.fl': '*',
                                          'hl.simple.pre': '<span class="highlight">',
                                          'hl.simple.post': '</span>'}))
    return search


def get_results(response):
    results = []
    # iterate over docs
    for doc in response:
        # iterate over every key in single doc dictionary
        for key in doc:
            if key in response.highlighting[doc['id']]:
                doc[key] = response.highlighting[doc['id']][key]
        results.append(doc)
    return results


if __name__ == '__main__':
    term = "film"
    print("Search films | term = " + term + ":\n", solr_search(core="films", term=term))
