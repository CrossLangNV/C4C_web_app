import io
import itertools
import logging
import os
import shutil
from http.client import HTTPResponse
from operator import itemgetter
from wsgiref.util import FileWrapper
from zipfile import ZipFile
from django.http import HttpResponse

import requests
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from jsonlines import jsonlines
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .datahandling import sync_documents, sync_attachments, score_documents
from .forms import DocumentForm, WebsiteForm
from .models import Website, Document, Attachment, AcceptanceState, AcceptanceStateValue, Comment, Tag
from .permissions import IsOwner, IsOwnerOrSuperUser
from .serializers import AttachmentSerializer, DocumentSerializer, WebsiteSerializer, AcceptanceStateSerializer, \
    CommentSerializer, TagSerializer
from .solr_call import solr_search, solr_search_id, solr_search_website_sorted, solr_search_document_id_sorted

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))


class DocumentSearchView(TemplateView):
    template_name = "searchapp/document_search.html"
    search_term = "*"
    results = []

    def get(self, request, *args, **kwargs):
        if request.GET.get('term'):
            self.search_term = request.GET['term']

        self.results = solr_search(core="documents", term=self.search_term)
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
        django_documents = Document.objects.filter(
            website=website).order_by('id')
        sync = self.request.GET.get('sync', False)
        if sync:
            # query Solr for available documents and sync with Django
            solr_documents = solr_search_website_sorted(
                core='documents', website=website.name.lower())
            sync_documents(website, solr_documents, django_documents)
        score = self.request.GET.get('score', False)
        if score:
            # get confidence score
            score_documents(django_documents)
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
        solr_files = solr_search_document_id_sorted(
            core='files', document_id=str(document.id))
        django_attachments = Attachment.objects.filter(
            document=document).order_by('id')
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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        queryset = Website.objects.all()
        return queryset


class WebsiteDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    logger = logging.getLogger(__name__)

    def get_object(self):
        self.logger.info("In website detail view")
        queryset = self.get_queryset()
        website_qs = queryset.filter(pk=self.kwargs['pk'])
        website = website_qs[0]
        django_documents = Document.objects.filter(
            website=website).order_by('id')
        sync = self.request.GET.get('sync', False)
        if sync:
            solr_documents = solr_search_website_sorted(
                core='documents', website=website.name.lower())
            sync_documents(website, solr_documents, django_documents)
        else:
            self.logger.info("Not syncing")
        score = self.request.GET.get('score', False)
        if score:
            # get confidence score
            score_documents(django_documents)

        return website


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 1000


class DocumentListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DocumentSerializer
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        q = Document.objects.all()
        keyword = self.request.GET.get('keyword', "")
        if keyword:
            q = q.filter(title__icontains=keyword)
        showonlyown = self.request.GET.get('showOnlyOwn', "")
        if showonlyown == "true":
            username = self.request.GET.get('userName', "")
            q = q.filter(Q(acceptance_states__user__username=username) & (Q(acceptance_states__value="Accepted") |
                                                                          Q(acceptance_states__value="Rejected")))
        filtertype = self.request.GET.get('filterType', "")
        if filtertype == "unvalidated":
            q = q.exclude(Q(acceptance_states__value="Rejected")
                          | Q(acceptance_states__value="Accepted"))
        if filtertype == "accepted":
            q = q.filter(acceptance_states__value="Accepted").distinct()
        if filtertype == "rejected":
            q = q.filter(acceptance_states__value="Rejected").distinct()
        website = self.request.GET.get('website', "")
        if website:
            q = q.filter(website__name__iexact=website)
        tag = self.request.GET.get('tag', "")
        if tag:
            q = q.filter(tags__value=tag)
        return q.order_by("-created_at")


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
            solr_files = solr_search_document_id_sorted(
                core='files', document_id=str(document.id))
            django_attachments = Attachment.objects.filter(
                document=document).order_by('id')
            if sync:
                sync_attachments(document, solr_files, django_attachments)
        return document


class AttachmentListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


class AttachmentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def get_object(self):
        queryset = self.get_queryset()
        attachment_qs = queryset.filter(pk=self.kwargs['pk'])
        attachment = attachment_qs[0]
        solr_attachment = solr_search_id(
            core='files', id=str(attachment.id))[0]
        if not attachment.content and "content" in solr_attachment:
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


class CommentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperUser]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def put(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.update(request, *args, **kwargs)


class TagListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


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


class ExportDocuments(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        websites = Website.objects.all()
        for website in websites:
            if not os.path.exists(workpath + '/export/jsonl/' + website.name):
                os.makedirs(workpath + '/export/jsonl/' + website.name)
            documents = solr_search(
                core='documents', term='website:' + website.name)
            for document in documents:
                files = solr_search_document_id_sorted(
                    core='files', document_id=document['id'])
                with jsonlines.open(workpath + '/export/jsonl/' + website.name + '/doc_' + document['id'] + '.jsonl',
                                    mode='w') as f:
                    f.write(document)
                    for file in files:
                        f.write(file)

        # create zip file for all .jsonl files
        zip_filename = 'exported_docs.zip'
        # open BytesIO to grab in-memory ZIP contents
        b = io.BytesIO()
        zf = ZipFile(b, "w")
        for root, subfolders, filenames in os.walk(workpath + '/export/jsonl'):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                zf.write(file_path, os.path.relpath(
                    file_path, workpath + '/export/jsonl'))
        zf.close()
        # clear export folder
        for filename in os.listdir(workpath + '/export'):
            file_path = os.path.join(workpath + '/export', filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error('Failed to delete %s. Reason: %s' %
                             (file_path, e))
        # return zip
        response = HttpResponse(
            b.getvalue(), content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename="%s"' % zip_filename
        return response


@api_view(['GET'])
def celex_get_xhtml(request):
    if request.method == 'GET':
        celex_id = request.GET["celex_id"]
        logger.info(celex_id)
        headers = {"Accept": "application/xhtml+xml", "Accept-Language": "eng"}
        response = requests.get(
            "http://publications.europa.eu/resource/celex/" + celex_id, headers=headers)
        if response.status_code != 200:
            headers = {"Accept": "text/html", "Accept-Language": "eng"}
            response = requests.get(
                "http://publications.europa.eu/resource/celex/" + celex_id, headers=headers)
        return Response(response.text)


@api_view(['GET'])
def document_stats(request):
    if request.method == 'GET':
        q1 = Document.objects.all()
        q2 = q1.exclude(Q(acceptance_states__value="Rejected")
                        | Q(acceptance_states__value="Accepted"))
        q3 = q1.filter(acceptance_states__value="Accepted").distinct()
        q4 = q1.filter(acceptance_states__value="Rejected").distinct()
        q5 = q1.filter(Q(acceptance_states__value="Rejected") & Q(
            acceptance_states__probability_model__isnull=False))
        q6 = q1.filter(Q(acceptance_states__value="Accepted") & Q(
            acceptance_states__probability_model__isnull=False))

        return Response({
            'count_total': len(q1),
            'count_unvalidated': len(q2),
            'count_accepted': len(q3),
            'count_rejected': len(q4),
            'count_autorejected': len(q5),
            'count_autovalidated': len(q6),
        })
