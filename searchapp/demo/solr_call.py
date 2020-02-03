import pysolr

def solr_search(name="", cat=""):
    client = pysolr.Solr('http://localhost:8983/solr/demo')
    search = get_results(client.search('name:' + name, **{'rows': 100, 'hl': 'true'}))
    return search

def get_results(response):
    # parse
    results = []
    for result in response:
        results.append(result)
    return results

if __name__ == '__main__':
    print("Search demo | name = game:\n", solr_search(name = "game"))