from django.shortcuts import render
from .solr_call import solr_search

from rest_framework.views import APIView
from rest_framework.response import Response

def search_index(request):
    search_term = "*"
    if request.GET.get('term'):
        search_term = request.GET['term']

    results = solr_search(core="films", term=search_term)
    print(results)
    context = {'results': results, 'count': len(results), 'search_term': search_term}
    return render(request, 'index.html', context)

class FilmList(APIView):
    """
    View all films.
    """
    def get(self, request, format=None):
        """
        Return a list of all films.
        """
        films = solr_search(core="films", term="*")
        return Response(films)

class Film(APIView):
    """
    Search for a film.
    """
    def get(self, request, search_term, format=None):
        """
        Return a list of found films.
        """
        films = solr_search(core="films", term=search_term)
        return Response(films)

