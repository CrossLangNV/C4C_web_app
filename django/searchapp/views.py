import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from rest_framework import permissions
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .datahandling import sync_documents, sync_attachments
from .forms import DocumentForm, WebsiteForm
from .models import Website, Document, Attachment, AcceptanceState, AcceptanceStateValue, Comment
from .permissions import IsOwner
from .serializers import AttachmentSerializer, DocumentSerializer, WebsiteSerializer, AcceptanceStateSerializer, \
    CommentSerializer
from .solr_call import solr_search, solr_search_id, solr_search_website_sorted, solr_search_document_id_sorted


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
        website = Website.objects.get(pk=self.kwargs['pk'])
        django_documents = Document.objects.filter(website=website).order_by('id')
        sync = self.request.GET.get('sync', False)
        if sync:
            # query Solr for available documents and sync with Django
            solr_documents = solr_search_website_sorted(core='documents', website=website.name.lower())
            sync_documents(website, solr_documents, django_documents)
        # add to context to be used in template
        context['documents'] = django_documents
        return context


class DocumentDetailView(PermissionRequiredMixin, DetailView):
    model = Document
    template_name = 'searchapp/document_detail.html'
    context_object_name = 'document'
    permission_required = 'searchapp.view_document'

    def get_context_data(self, **kwargs):
        # call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        document = Document.objects.get(id=self.kwargs['pk'])
        # sync current document
        solr_document = solr_search_id(core='documents', id=str(document.id))
        sync_documents(document.website, solr_document, [document])
        # query Solr for attachments
        solr_files = solr_search_document_id_sorted(core='files', document_id=str(document.id))
        django_attachments = Attachment.objects.filter(document=document).order_by('id')
        sync_attachments(document, solr_files, django_attachments)
        context['attachments'] = django_attachments
        return context


class DocumentUpdateView(UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'searchapp/document_update.html'
    context_object_name = 'document'

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
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        queryset = Website.objects.all()
        return queryset


class WebsiteDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    logger = logging.getLogger(__name__)

    def get_object(self):
        queryset = self.get_queryset()
        website_qs = queryset.filter(pk=self.kwargs['pk'])
        website = website_qs[0]
        django_documents = Document.objects.filter(website=website).order_by('id')
        sync = self.request.GET.get('sync', False)
        if sync:
            solr_documents = solr_search_website_sorted(core='documents', website=website.name.lower())
            sync_documents(website, solr_documents, django_documents)
        return website


class DocumentListAPIView(ListCreateAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        queryset = Document.objects.all()
        return queryset


class DocumentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_object(self):
        queryset = self.get_queryset()
        document_qs = queryset.filter(pk=self.kwargs['pk'])
        document = document_qs[0]
        with_attachments = self.request.GET.get('with_attachments', False)
        sync = self.request.GET.get('sync', False)
        solr_document = solr_search_id(core='documents', id=str(document.id))
        if sync:
            sync_documents(document.website, solr_document, [document])
        if with_attachments:
            # query Solr for attachments
            solr_files = solr_search_document_id_sorted(core='files', document_id=str(document.id))
            django_attachments = Attachment.objects.filter(document=document).order_by('id')
            if sync:
                sync_attachments(document, solr_files, django_attachments)
        return document


class AttachmentListAPIView(ListCreateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


class AttachmentDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def get_object(self):
        queryset = self.get_queryset()
        attachment_qs = queryset.filter(pk=self.kwargs['pk'])
        attachment = attachment_qs[0]
        solr_attachment = solr_search_id(core='files', id=str(attachment.id))[0]
        if not attachment.content:
            attachment.content = solr_attachment['content']
        return attachment


class AcceptanceStateValueAPIView(APIView):

    def get(self, request, format=None):
        return Response([state.value for state in AcceptanceStateValue])


class AcceptanceStateListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AcceptanceStateSerializer

    def list(self, request, *args, **kwargs):
        queryset = AcceptanceState.objects.filter(user=request.user)
        serializer = AcceptanceStateSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.create(request, *args, **kwargs)


class AcceptanceStateDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    serializer_class = AcceptanceStateSerializer
    queryset = AcceptanceState.objects.all()

    def put(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.update(request, *args, **kwargs)


class CommentListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommentSerializer

    def list(self, request, *args, **kwargs):
        queryset = Comment.objects.filter(user=request.user)
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.create(request, *args, **kwargs)


class CommentDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def put(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.update(request, *args, **kwargs)


class IsSuperUserAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        is_superuser = request.user.is_superuser

        return Response(is_superuser)


class SolrFileList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        files = solr_search(core="files", term="*")
        return Response(files)


class SolrFile(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, search_term, format=None):
        files = solr_search(core="files", term=search_term)
        return Response(files)


class SolrDocument(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id, format=None):
        solr_document = solr_search_id(core='documents', id=id)
        return Response(solr_document)


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
