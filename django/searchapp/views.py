from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import DocumentForm, WebsiteForm
from .models import Website, Document, Attachment
from .serializers import AttachmentSerializer, DocumentSerializer, WebsiteSerializer
from .solr_call import solr_search, solr_search_id


class FilmSearchView(TemplateView):
    template_name = "searchapp/film_search.html"
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


class DocumentSearchView(TemplateView):
    template_name = "searchapp/document_search.html"
    search_term = "*"
    results = []

    def get(self, request, *args, **kwargs):
        if request.GET.get('term'):
            self.search_term = request.GET['term']

        self.results = solr_search(core="documents", term=self.search_term)
        print(self.results)
        context = {'results': self.results, 'count': len(self.results), 'search_term': self.search_term,
                   'nav': 'documents'}
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
                doc.solr_data = solr_data[0]
        # add to context to be used in template
        context['documents'] = documents
        return context


class DocumentDetailView(PermissionRequiredMixin, DetailView):
    model = Document
    template_name = 'searchapp/document_detail.html'
    context_object_name = 'document'
    permission_required = 'searchapp.view_document'

    def get_context_data(self, **kwargs):
        # call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # which subclass of Document depends on its Website
        document = Document.objects.get(id=self.kwargs['pk'])
        document_type = document.website.name.lower() + 'document'
        document = Document.objects.select_related(document_type).get(id=self.kwargs['pk'])
        sub_doc = getattr(document, document_type)

        # add in the Solr data to document
        solr_data = solr_search_id('documents', str(sub_doc.id))
        if solr_data:
            sub_doc.solr_data = solr_data[0]
        # add to context to be used in template
        context['document'] = sub_doc
        return context


class DocumentUpdateView(UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'searchapp/document_update.html'
    context_object_name = 'document'

    def get_initial(self):
        initial = super().get_initial()
        document = Document.objects.get(id=self.kwargs['pk'])
        solr_data = solr_search_id('documents', str(document.id))
        if solr_data:
            initial['content'] = solr_data[0]['content'][0]
        return initial

    def get_success_url(self):
        return reverse_lazy('searchapp:document', kwargs={'pk': self.kwargs['pk']})


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "searchapp/document_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.website = Website.objects.get(pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('searchapp:website', kwargs={'pk': self.website.id})

    def form_valid(self, form):
        form.instance.website = self.website
        return super().form_valid(form)


class DocumentDeleteView(DeleteView):
    model = Document
    template_name = "searchapp/document_delete.html"
    context_object_name = 'document'

    def get_success_url(self):
        document = Document.objects.get(pk=self.kwargs['pk'])
        return reverse_lazy('searchapp:website', kwargs={'pk': document.website.id})


class WebsiteUpdateView(UpdateView):
    model = Website
    form_class = WebsiteForm
    template_name = "searchapp/website_update.html"
    context_object_name = 'website'

    def get_success_url(self):
        return reverse_lazy('searchapp:website', kwargs={'pk': self.kwargs['pk']})


class WebsiteCreateView(CreateView):
    model = Website
    form_class = WebsiteForm
    success_url = reverse_lazy('searchapp:websites')
    template_name = "searchapp/website_create.html"


class WebsiteDeleteView(DeleteView):
    model = Website
    success_url = reverse_lazy('searchapp:websites')
    template_name = 'searchapp/website_delete.html'
    context_object_name = 'website'


class WebsiteListAPIView(ListCreateAPIView):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer


class WebsiteDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer


class DocumentListAPIView(ListCreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class DocumentDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class AttachmentListAPIView(ListCreateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


class AttachmentDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


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
