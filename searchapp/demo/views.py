from django.shortcuts import render
from .solr_call import solr_search

def search_index(request):
    search_term = "*"
    if request.GET.get('term'):
        search_term = request.GET['term']

    results = solr_search(core="films", term=search_term)
    print(results)
    context = {'results': results, 'count': len(results), 'search_term': search_term}
    return render(request, 'index.html', context)
