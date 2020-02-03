from django.shortcuts import render
from .solr_call import solr_search

def search_index(request):
    name_term = "*"
    if request.GET.get('name'):
        name_term = request.GET['name']
    search_term = name_term
    results = solr_search(name=name_term)
    print(results)
    context = {'results': results, 'count': len(results), 'search_term': search_term}
    return render(request, 'index.html', context)
