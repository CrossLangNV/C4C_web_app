import json
import logging
import os
import re

import requests
from celery.result import AsyncResult
from django.db.models import Q, Count
from django.db.models.functions import Length
from django.http import FileResponse
from lxml import html
from minio import Minio
from rest_framework import permissions, filters, status
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from scheduler.tasks import export_documents, sync_documents_task, score_documents_task
from scheduler.tasks_single import full_service_single
from .models import Website, Document, Attachment, AcceptanceState, AcceptanceStateValue, Comment, Tag, Bookmark
from .permissions import IsOwner, IsOwnerOrSuperUser
from .serializers import AttachmentSerializer, DocumentSerializer, WebsiteSerializer, AcceptanceStateSerializer, \
    CommentSerializer, TagSerializer, BookmarkSerializer
from .solr_call import solr_search_id, solr_search_paginated, solr_search_query_paginated, solr_mlt, \
    solr_search_query_paginated_preanalyzed, solr_search_ids, solr_get_preanalyzed_for_doc, solr_search_query_with_doc_id_preanalyzed

from glossary.models import Concept, ConceptOccurs, ConceptDefined

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))
export_path = '/django/scheduler/export/'


class WebsiteListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        queryset = Website.objects.annotate(
            total_documents=Count(
                'documents', filter=Q(documents__title__gt=''))
        )
        return queryset


class WebsiteDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WebsiteSerializer
    logger = logging.getLogger(__name__)

    def get_queryset(self):
        queryset = Website.objects.annotate(
            total_documents=Count(
                'documents', filter=Q(documents__title__gt=''))
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
        keyword = self.request.GET.get('keyword', "")
        showonlyown = self.request.GET.get('showOnlyOwn', "")
        bookmarks = self.request.GET.get('bookmarks', "")
        celex = self.request.GET.get('celex', "")
        type = self.request.GET.get('type', "")
        status = self.request.GET.get('status', "")
        eli = self.request.GET.get('eli', "")
        author = self.request.GET.get('author', "")
        date_of_effect = self.request.GET.get('date_of_effect', "")
        username = self.request.GET.get('username', "")
        website = self.request.GET.get('website', "")
        tag = self.request.GET.get('tag', "")
        filtertype = self.request.GET.get('filterType', "")

        q = Document.objects.annotate(
            text_len=Length('title')).filter(text_len__gt=1)

        if len(keyword) > 0:
            solr_query = f"id:\"{keyword}\" OR title:\"{keyword}\" OR content:\"{keyword}\" OR celex:\"{keyword}\""
            solr_result = solr_search_ids("documents", solr_query)

            id_list = []
            for doc in solr_result:
                id_list.append(doc['id'])

            if len(id_list) > 0:
                q = q.filter(id__in=id_list)
            else:
                if keyword:
                    q = q.filter(title__icontains=keyword)

        if showonlyown == "true":
            q = q.filter(Q(acceptance_states__user__username=username) & (Q(acceptance_states__value="Accepted") |
                                                                          Q(acceptance_states__value="Rejected")))
        if bookmarks == "true":
            q = q.filter(bookmarks__user__username=username)

        if celex:
            q = q.filter(celex__exact=celex)

        if type:
            q = q.filter(type__exact=type)

        if status:
            q = q.filter(status__exact=status)

        if eli:
            q = q.filter(eli__exact=eli)

        if author:
            q = q.filter(author__exact=author)

        if date_of_effect:
            q = q.filter(date_of_effect__exact=date_of_effect)

        if website:
            q = q.filter(website__name__iexact=website)

        if tag:
            q = q.filter(tags__value=tag)

        if filtertype == "unvalidated":
            q = q.filter(unvalidated=True)
        elif filtertype == "accepted":
            q = q.filter(acceptance_states__value="Accepted").distinct()
        elif filtertype == "rejected":
            q = q.filter(acceptance_states__value="Rejected").distinct()
        return q

    def create(self, request, *args, **kwargs):
        response = super(DocumentListAPIView, self).create(
            request, *args, **kwargs)
        full_service_single.delay(response.data['id'])
        return response


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
    logger = logging.getLogger(__name__)

    def list(self, request, *args, **kwargs):
        queryset = AcceptanceState.objects.filter(user=request.user)
        serializer = AcceptanceStateSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        document = Document.objects.get(pk=request.data['document'])
        AcceptanceState.objects.update_or_create(
            document=document, user=request.user, defaults={'value': request.data['value']})
        return Response("ok")


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


class SolrDocumentSearch(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, search_term, format=None):
        result = solr_search_paginated(core="documents", term=search_term, page_number=request.GET.get('pageNumber', 1),
                                       rows_per_page=request.GET.get(
                                           'pageSize', 1),
                                       ids_to_filter_on=request.GET.getlist(
                                           'id'),
                                       sort_by=request.GET.get('sortBy'),
                                       sort_direction=request.GET.get('sortDirection'))
        return Response(result)


class SolrDocumentsSearchQueryPreAnalyzed(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        result = solr_search_query_paginated_preanalyzed(core="documents", term=request.data['query'],
                                                         page_number=request.GET.get(
                                                             'pageNumber', 1),
                                                         rows_per_page=request.GET.get(
                                                             'pageSize', 1),
                                                         sort_by=request.GET.get(
                                                             'sortBy'),
                                                         sort_direction=request.GET.get('sortDirection'))
        return Response(result)

class SolrDocumentSearchQueryPreAnalyzed(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doc_id, format=None):
        result = solr_search_query_with_doc_id_preanalyzed(doc_id=doc_id, core="documents", term=request.data['query'],
                                                         page_number=request.GET.get('pageNumber', 1),
                                                         rows_per_page=request.GET.get(
                                                             'pageSize', 1),
                                                         sort_by=request.GET.get('sortBy'),
                                                         sort_direction=request.GET.get('sortDirection'))
        return Response(result)

class SolrDocumentsSearchQueryDjango(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):

        concept = Concept.objects.get(pk=request.data['id'])

        concept_defined_or_occurs = None
        if request.data['field'] == "concept_defined":
            concept_defined_or_occurs = ConceptDefined.objects.filter(
                concept=concept)
        else:
            concept_defined_or_occurs = ConceptOccurs.objects.filter(
                concept=concept)

        definitions = []
        for defi_or_occ in concept_defined_or_occurs:

            highlighting = solr_get_preanalyzed_for_doc(core="documents",
                                                        id=defi_or_occ.document.id,
                                                             field=request.data['field'],
                                                             term=request.data['term'],
                                                             page_number=request.GET.get(
                                                                 'pageNumber', 1),
                                                             rows_per_page=request.GET.get(
                                                                 'pageSize', 1),
                                                             sort_by=request.GET.get(
                                                                 'sortBy'),
                                                             sort_direction=request.GET.get('sortDirection'))
            definitions.append({"title": defi_or_occ.document.title, "date": str(defi_or_occ.document.date), "id": str(defi_or_occ.document.id),
                                "website": str(defi_or_occ.document.website), request.data['field']: highlighting})

        response = [len(definitions), definitions]

        return Response(response)


class SimilarDocumentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        similar_document_ids_with_coeff = solr_mlt('documents', str(id),
                                                   number_candidates=request.GET.get(
                                                       'numberCandidates', 5),
                                                   threshold=request.GET.get('threshold', 0.0))
        formatted_response = []
        for id, title, website, coeff in similar_document_ids_with_coeff:
            formatted_response.append(
                {'id': id, 'title': title, 'website': website, 'coefficient': coeff})
        return Response(formatted_response)


class FormexUrlsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, celex):
        return Response(get_formex_urls(celex))


class FormexActAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
    headers = {'Accept': 'application/list;mtype=fmx4',
               'Accept-Language': 'eng'}
    response = requests.get(cellar_api + celex, headers=headers)
    formex_links = []
    if response.status_code == 200:
        html_content = response.content
        tree = html.fromstring(html_content)
        # only links that point to an .xml document
        formex_links = tree.xpath('//a/*[contains(text(),".xml")]/../@href')
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


class BookmarkListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookmarkSerializer

    def post(self, request):
        user = request.user
        document = Document.objects.get(pk=request.data['document'])
        bookmark = Bookmark.objects.create(user=user, document=document)
        serializer = BookmarkSerializer(bookmark)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CelexListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        celex_objects = Document.objects.order_by('celex').values_list('celex', flat=True).distinct('celex')

        options = [{"name": "CELEX", "code": ""}]
        for celex in celex_objects:
            options.append({"name": celex, "code": celex})

        return Response(options)


class TypeListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        type_objects = Document.objects.order_by('type').values_list('type', flat=True).distinct('type')

        options = [{"name": "Type", "code": ""}]
        for t in type_objects:
            options.append({"name": t, "code": t})

        return Response(options)


class StatusListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        status_objects = Document.objects.order_by('status').values_list('status', flat=True).distinct('status')

        options = [{"name": "Status", "code": ""}]
        for s in status_objects:
            options.append({"name": s, "code": s})

        return Response(options)


class EliListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        eli_objects = Document.objects.order_by('eli').values_list('eli', flat=True).distinct('eli')

        options = [{"name": "ELI", "code": ""}]
        for e in eli_objects:
            options.append({"name": e, "code": e})

        return Response(options)


class AuthorListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        author_objects = Document.objects.order_by('author').values_list('author', flat=True).distinct('author')

        options = [{"name": "Author", "code": ""}]
        for a in author_objects:
            options.append({"name": a, "code": a})

        return Response(options)


class DateOfEffectListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        date_objects = Document.objects.order_by('date_of_effect').values_list('date_of_effect', flat=True)\
                        .distinct('date_of_effect')

        options = [{"name": "In Force Date", "code": ""}]
        for d in date_objects:
            options.append({"name": d, "code": d})

        return Response(options)


class BookmarkDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    logger = logging.getLogger(__name__)

    def delete(self, request, document_id):
        user = request.user
        document = Document.objects.get(pk=document_id)
        bookmark = Bookmark.objects.filter(user=user, document=document)
        bookmark.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)
