import logging
import os
import re

import requests
from bs4 import BeautifulSoup
from celery.result import AsyncResult
from django.db.models import Q, Count
from django.db.models.functions import Length
from django.http import FileResponse
from minio import Minio
from rest_framework import permissions, filters, status
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from scheduler.tasks import export_documents, sync_documents_task, score_documents_task
from .models import Website, Document, Attachment, AcceptanceState, AcceptanceStateValue, Comment, Tag
from .permissions import IsOwner, IsOwnerOrSuperUser
from .serializers import AttachmentSerializer, DocumentSerializer, WebsiteSerializer, AcceptanceStateSerializer, \
    CommentSerializer, TagSerializer
from .solr_call import solr_search_id, solr_search_paginated, solr_search_query_paginated, solr_mlt, \
    solr_search_query_paginated_preanalyzed

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))
export_path = '/django/scheduler/export/'


class WebsiteListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        queryset = Website.objects.annotate(
            total_documents=Count('documents', filter=Q(documents__deleted__isnull=True) &
                                                      Q(documents__title__gt=''))
        )
        return queryset


class WebsiteDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WebsiteSerializer
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        queryset = Website.objects.annotate(
            total_documents=Count('documents', filter=Q(documents__deleted__isnull=True) &
                                                      Q(documents__title__gt=''))
        )
        return queryset

    def get_object(self):
        self.logger.info("In website detail view")
        website = self.get_queryset().get(pk=self.kwargs['pk'])
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
        q = Document.objects.annotate(
            text_len=Length('title')).filter(text_len__gt=1)
        keyword = self.request.GET.get('keyword', "")
        if keyword:
            q = q.filter(title__icontains=keyword)
        showonlyown = self.request.GET.get('showOnlyOwn', "")
        if showonlyown == "true":
            email = self.request.GET.get('email', "")
            q = q.filter(Q(acceptance_states__user__email=email) & (Q(acceptance_states__value="Accepted") |
                                                                    Q(acceptance_states__value="Rejected")))
        website = self.request.GET.get('website', "")
        if website:
            q = q.filter(website__name__iexact=website)
        tag = self.request.GET.get('tag', "")
        if tag:
            q = q.filter(tags__value=tag)
        filtertype = self.request.GET.get('filterType', "")
        if filtertype == "unvalidated":
            q = q.filter(unvalidated=True)
        elif filtertype == "accepted":
            q = q.filter(acceptance_states__value="Accepted").distinct()
        elif filtertype == "rejected":
            q = q.filter(acceptance_states__value="Rejected").distinct()
        return q


class DocumentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_object(self):
        document = Document.objects.get(pk=self.kwargs['pk'])
        with_content = self.request.GET.get('with_content', False)
        if with_content:
            solr_doc = solr_search_id(
                core='documents', id=str(self.kwargs['pk']))[0]
            # Content is a virtual field (see serializer)
            if 'content' in solr_doc and len(solr_doc['content']) > 0:
                document.content = solr_doc['content'][0]
            if 'content_html' in solr_doc and len(solr_doc['content_html']) > 0:
                document.content = solr_doc['content_html'][0]
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
        # Read content from document
        queryset = self.get_queryset()
        attachment = Attachment
        solr_doc = solr_search_id(
            core='document', id=str(self.kwargs['pk']))[0]
        attachment.content = solr_doc['content']
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


class SolrDocumentSearch(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, search_term, format=None):
        result = solr_search_paginated(core="documents", term=search_term, page_number=request.GET.get('pageNumber', 1),
                                       rows_per_page=request.GET.get(
                                           'pageSize', 1),
                                       ids_to_filter_on=request.GET.getlist(
                                           'id'),
                                       sort_by=request.GET.get('sortBy'),
                                       sort_direction=request.GET.get('sortDirection'))
        return Response(result)


class SolrDocumentSearchQuery(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, search_term, format=None):
        result = solr_search_query_paginated(core="documents", term=search_term,
                                             page_number=request.GET.get('pageNumber', 1),
                                             rows_per_page=request.GET.get(
                                                 'pageSize', 1),
                                             ids_to_filter_on=request.GET.getlist(
                                                 'id'),
                                             sort_by=request.GET.get('sortBy'),
                                             sort_direction=request.GET.get('sortDirection'))
        return Response(result)


class SolrDocumentsSearchQueryPreAnalyzed(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        result = solr_search_query_paginated_preanalyzed(core="documents", term=request.data['query'],
                                                         page_number=request.GET.get('pageNumber', 1),
                                                         rows_per_page=request.GET.get(
                                                             'pageSize', 1),
                                                         sort_by=request.GET.get('sortBy'),
                                                         sort_direction=request.GET.get('sortDirection'))
        return Response(result)


class SimilarDocumentsAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        similar_document_ids_with_coeff = solr_mlt('documents', str(id),
                                                   number_candidates=request.GET.get('numberCandidates', 5),
                                                   threshold=request.GET.get('threshold', 0.0))
        formatted_response = []
        for id, title, website, coeff in similar_document_ids_with_coeff:
            formatted_response.append({'id': id, 'title': title, 'website': website, 'coefficient': coeff})
        return Response(formatted_response)


class FormexUrlsAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, celex):
        return Response(get_formex_urls(celex))


class FormexActAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, celex):
        formex_act = ''
        formex_links = get_formex_urls(celex)
        if len(formex_links) > 1:
            act_response = requests.get(formex_links[1])
            if act_response.status_code == 200:
                formex_act = act_response.content
        return Response(formex_act)


def get_formex_urls(celex):
    cellar_api = 'http://publications.europa.eu/resource/celex/'
    headers = {'Accept': 'application/list;mtype=fmx4', 'Accept-Language': 'eng'}
    response = requests.get(cellar_api + celex, headers=headers)
    formex_links = []
    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        formex_links = [link.get('href') for link in soup.findAll('a')]
        # sort Formex link on DOC number
        formex_links.sort(key=natural_keys)

    return formex_links


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [atoi(c) for c in re.split(r'(\d+)', text)]


class ExportDocumentsLaunch(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        task = export_documents.delay()
        response = {"task_id": task.task_id}
        return Response(response, status=status.HTTP_202_ACCEPTED)


class ExportDocumentsStatus(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id, format=None):
        result = AsyncResult(task_id)
        return Response(result.status, status=status.HTTP_200_OK)


class ExportDocumentsDownload(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id, format=None):
        # get zip for given task id from minio
        minio_client = Minio('minio:9000', access_key=os.environ['MINIO_ACCESS_KEY'],
                             secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
        file = minio_client.get_object('export', task_id + '.zip')
        response = FileResponse(file, as_attachment=True)
        response['Content-Disposition'] = 'attachment; filename="%s"' % 'exported_docs.zip'
        return response


@api_view(['GET'])
def document_stats(request):
    if request.method == 'GET':
        q1 = AcceptanceState.objects.all().order_by("document").distinct("document_id").annotate(
            text_len=Length('document__title')).filter(text_len__gt=1)
        q2 = q1.exclude(Q(value="Rejected") | Q(value="Accepted")
                        & Q(probability_model__isnull=True))
        q3 = q1.filter(Q(value="Accepted") & Q(probability_model__isnull=True))
        q4 = q1.filter(Q(value="Rejected") & Q(probability_model__isnull=True))
        q5 = q1.filter(Q(value="Unvalidated") & Q(
            probability_model__isnull=False))
        q6 = q1.filter(Q(value="Accepted") & Q(
            probability_model__isnull=False))
        q7 = q1.filter(Q(value="Rejected") & Q(
            probability_model__isnull=False))

        return Response({
            'count_total': q1.count(),
            'count_unvalidated': q2.count(),
            'count_accepted': q3.count(),
            'count_rejected': q4.count(),
            'count_autounvalidated': q5.count(),
            'count_autoaccepted': q6.count(),
            'count_autorejected': q7.count()
        })


@api_view(['GET'])
def count_total_documents(request):
    if request.method == 'GET':
        q = Document.objects.annotate(
            text_len=Length('title')).filter(text_len__gt=1).count()
        return Response(q)
