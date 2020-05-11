import logging
import os
from urllib.parse import quote

import requests
from celery.result import AsyncResult
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from minio import Minio
from rest_framework import permissions, filters, status
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from scheduler.tasks import export_documents, export_delete, sync_documents_task, score_documents_task
from .datahandling import sync_documents, sync_attachments
from .forms import DocumentForm, WebsiteForm
from .models import Website, Document, Attachment, AcceptanceState, AcceptanceStateValue, Comment, Tag
from .permissions import IsOwner, IsOwnerOrSuperUser
from .serializers import AttachmentSerializer, DocumentSerializer, WebsiteSerializer, AcceptanceStateSerializer, \
    CommentSerializer, TagSerializer
from .solr_call import solr_search, solr_search_id, solr_search_document_id_sorted, \
    solr_search_paginated

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))
export_path = '/django/scheduler/export/'


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
        sync = self.request.GET.get('sync', False)
        if sync:
            # query Solr for available documents and sync with Django
            sync_documents_task.delay(website.id)
        score = self.request.GET.get('score', False)
        if score:
            # get confidence score
            score_documents_task.delay(website.id)
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
        website = Website.objects.get(pk=self.kwargs['pk'])
        sync = self.request.GET.get('sync', False)
        if sync:
            sync_documents_task(website.id)
        else:
            self.logger.info("Not syncing")
        score = self.request.GET.get('score', False)
        if score:
            # get confidence score
            score_documents_task(website.id)
        else:
            self.logger.info("Not scoring")

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
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['title', 'date', 'acceptance_state_max_probability']

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
        document = Document.objects.get(pk=self.kwargs['pk'])
        with_attachments = self.request.GET.get('with_attachments', False)
        sync = self.request.GET.get('sync', False)
        if sync:
            solr_document = solr_search_id(
                core='documents', id=str(document.id))
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
        result = solr_search_paginated(core="files", term='*', page_number=request.GET.get('pageNumber', 1),
                                       rows_per_page=request.GET.get('pageSize', 1))
        return Response(result)


class SolrFile(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, search_term, format=None):
        result = solr_search_paginated(core="files", term=search_term, page_number=request.GET.get('pageNumber', 1),
                                       rows_per_page=request.GET.get('pageSize', 1))
        return Response(result)


class SolrDocument(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id, format=None):
        solr_document = solr_search_id(core='documents', id=id)
        return Response(solr_document)


class ExportDocumentsLaunch(APIView):

    def get(self, request, format=None):
        task = export_documents.delay()
        response = {"task_id": task.task_id}
        return Response(response, status=status.HTTP_202_ACCEPTED)


class ExportDocumentsStatus(APIView):

    def get(self, request, task_id, format=None):
        result = AsyncResult(task_id)
        return Response(result.status, status=status.HTTP_200_OK)


class ExportDocumentsDownload(APIView):

    def get(self, request, task_id, format=None):
        # get zip for given task id from minio
        minio_client = Minio('minio:9000', access_key=os.environ['MINIO_ACCESS_KEY'],
                             secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
        file = minio_client.get_object('export', task_id + '.zip')
        response = FileResponse(file, as_attachment=True)
        response['Content-Disposition'] = 'attachment; filename="%s"' % 'exported_docs.zip'
        # delete export contents
        export_delete.delay(task_id)
        return response


@api_view(['GET'])
def celex_get_xhtml(request):
    if request.method == 'GET':
        celex_id = quote(request.GET["celex_id"])
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
                        | Q(acceptance_states__value="Accepted") & Q(
            acceptance_states__probability_model__isnull=True))
        q3 = q1.filter(Q(acceptance_states__value="Accepted") & Q(
            acceptance_states__probability_model__isnull=True)).distinct()
        q4 = q1.filter(Q(acceptance_states__value="Rejected") & Q(
            acceptance_states__probability_model__isnull=True)).distinct()
        # FIXME: will be wrong when multiple auto-classifiers ?
        q5 = q1.filter(Q(acceptance_states__value="Unvalidated") & Q(
            acceptance_states__probability_model__isnull=False))
        q6 = q1.filter(Q(acceptance_states__value="Accepted") & Q(
            acceptance_states__probability_model__isnull=False))
        q7 = q1.filter(Q(acceptance_states__value="Rejected") & Q(
            acceptance_states__probability_model__isnull=False))

        return Response({
            'count_total': len(q1),
            'count_unvalidated': len(q2),
            'count_accepted': len(q3),
            'count_rejected': len(q4),
            'count_autounvalidated': len(q5),
            'count_autoaccepted': len(q6),
            'count_autorejected': len(q7),
        })
