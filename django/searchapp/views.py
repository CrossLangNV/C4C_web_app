from django.shortcuts import render
from django.urls import reverse_lazy
from .solr_call import solr_search, solr_search_id

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Document, Website
from .forms import DocumentForm, WebsiteForm

from django.views.generic import ListView, DetailView, CreateView, TemplateView


class FilmSearchView(TemplateView):
    template_name = "searchapp/index.html"
    search_term = "*"
    results = []

    def get(self, request, *args, **kwargs):
        if request.GET.get('term'):
            self.search_term = request.GET['term']

        self.results = solr_search(core="films", term=self.search_term)
        print(self.results)
        context = {'results': self.results, 'count': len(self.results), 'search_term': self.search_term,
                   'nav': 'films'}
        return render(request, self.template_name, context)


class WebsiteListView(ListView):
    model = Website
    template_name = 'website_list.html'
    context_object_name = 'websites'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav'] = 'websites'
        return context


class WebsiteDetailView(DetailView):
    model = Website
    template_name = 'searchapp/website_detail.html'
    context_object_name = 'website'

    def get_context_data(self, **kwargs):
        # call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add in the Solr data to documents
        documents = Document.objects.filter(website=self.kwargs['pk'])
        for doc in documents:
            solr_data = solr_search_id('documents', str(doc.id))
            if solr_data:
                doc.solr_data = solr_search_id('documents', str(doc.id))[0]
        # add to context to be used in template
        context['documents'] = documents
        return context


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "searchapp/document_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.website = Website.objects.get(pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('website', kwargs={'pk': self.website.id})

    def form_valid(self, form):
        form.instance.website = self.website
        return super().form_valid(form)


class WebsiteCreateView(CreateView):
    model = Website
    form_class = WebsiteForm
    success_url = reverse_lazy('websites')
    template_name = "searchapp/website_create.html"


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
