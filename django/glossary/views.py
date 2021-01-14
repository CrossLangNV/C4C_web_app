from rest_framework import permissions, filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from glossary.models import AcceptanceState, AcceptanceStateValue, Comment, Concept, Tag, AnnotationWorklog, ConceptOccurs, ConceptDefined
from glossary.serializers import AcceptanceStateSerializer, ConceptSerializer, TagSerializer, \
    AnnotationWorklogSerializer, ConceptOccursSerializer, ConceptDefinedSerializer
from glossary.serializers import AcceptanceStateSerializer, ConceptSerializer, TagSerializer, \
    AnnotationWorklogSerializer, ConceptOccursSerializer, ConceptDefinedSerializer, CommentSerializer
from scheduler.extract import send_document_to_webanno
from searchapp.models import Document, Bookmark
from searchapp.serializers import DocumentSerializer
from searchapp.solr_call import solr_search_paginated
from searchapp.permissions import IsOwner, IsOwnerOrSuperUser
from django.db.models import Q
import os
import logging as logger

import datetime

# Annotation API consants

ANNOTATION_STORE_METADATA = '{"message": "Annotator Store API","links": {}}'
KWARGS_ANNOTATION_TYPE_KEY = 'annotation_type'
KWARGS_ANNOTATION_TYPE_VALUE_OCCURENCE = 'occurence'
KWARGS_ANNOTATION_TYPE_VALUE_DEFINITION = 'definition'
KWARGS_CONCEPT_ID_KEY = 'concept_id'
KWARGS_DOCUMENT_ID_KEY = 'document_id'

class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConceptListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'acceptance_state_max_probability']

    def get_queryset(self):
        # TODO Remove the Unknown term and empty definition exclude filter
        q = Concept.objects.all().exclude(
            name__exact='Unknown').exclude(definition__exact='')
        keyword = self.request.GET.get('keyword', "")
        if keyword:
            q = q.filter(name__icontains=keyword)
        showonlyown = self.request.GET.get('showOnlyOwn', "")
        if showonlyown == "true":
            email = self.request.GET.get('email', "")
            q = q.filter(Q(acceptance_states__user__email=email) & (Q(acceptance_states__value="Accepted") |
                                                                    Q(acceptance_states__value="Rejected")))

        filtertype = self.request.GET.get('filterType', "")
        if filtertype == "unvalidated":
            q = q.exclude(Q(acceptance_states__value="Rejected")
                          | Q(acceptance_states__value="Accepted"))
        if filtertype == "accepted":
            q = q.filter(acceptance_states__value="Accepted").distinct()
        if filtertype == "rejected":
            q = q.filter(acceptance_states__value="Rejected").distinct()
        tag = self.request.GET.get('tag', "")
        if tag:
            q = q.filter(tags__value=tag)
        version = self.request.GET.get('version', "")
        if len(version):
            q = q.filter(version=version)

        website = self.request.GET.get('website', "")
        if len(website):
            q = q.filter(website__name__iexact=website)

        showbookmarked = self.request.GET.get('showBookmarked', "")
        if showbookmarked == "true":
            email = self.request.GET.get('email', "")
            bookmarks = Bookmark.objects.filter(user__username=email)
            bookmarked_documents = Document.objects.filter(bookmarks__in=bookmarks)
            q = Concept.objects.filter(document_defined__in=bookmarked_documents) | \
                Concept.objects.filter(document_occurs__in=bookmarked_documents)

        return q.order_by("name")


class ConceptDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer


class ConceptDocumentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, concept, format=None):
        files_result = solr_search_paginated(core="files", term=concept, page_number=request.GET.get('pageNumber', 1),
                                             rows_per_page=request.GET.get('pageSize', 100))
        files_result = list(files_result)
        documents = []
        for file in files_result[1]:
            doc_id = file['attr_document_id'][0]
            doc = Document.objects.get(id=doc_id)
            if doc:
                documents.append(doc)
        document_serializer = DocumentSerializer(
            instance=documents, many=True, context={'request': request})

        files_result.append(document_serializer.data)
        return Response(files_result)


class TagListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class WorkLogAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()


class WorklogDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()


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

@api_view(['GET'])
def get_distinct_versions(request):
    if request.method == 'GET':
        q = set(Concept.objects.values_list('version', flat=True))
        return Response(q)


@api_view(['GET'])
def get_webanno_link(request, document_id):
    doc = Document.objects.get(pk=document_id)
    if doc.webanno_document_id is None:
        webanno_doc = send_document_to_webanno(document_id)
        if webanno_doc is None:
            doc.webanno_document_id = None
            doc.webanno_project_id = None
            doc.save()
            return Response("404")

        doc.webanno_document_id = webanno_doc.document_id
        doc.webanno_project_id = webanno_doc.project_id
        doc.save()

    return Response(os.environ['WEBANNO_URL'] + "/annotation.html?50#!p="+str(doc.webanno_project_id) + "&d="+str(doc.webanno_document_id)+"&f=1")

# Terms and Definitions Annotations API

class RootAPIView(APIView):
    def get(self, request, annotation_type, concept_id, document_id, format=None):
        return Response(ANNOTATION_STORE_METADATA)

class SearchListAPIView(ListCreateAPIView):
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()

    def list(self, request, *args, **kwargs):
        annotation_worklogs = None
        if (self.kwargs[KWARGS_ANNOTATION_TYPE_KEY] == KWARGS_ANNOTATION_TYPE_VALUE_OCCURENCE):
            annotation_worklogs = AnnotationWorklog.objects\
                .filter(concept_occurs__concept__id=self.kwargs[KWARGS_CONCEPT_ID_KEY])\
                .filter(concept_occurs__document__id=self.kwargs[KWARGS_DOCUMENT_ID_KEY])
        elif (self.kwargs[KWARGS_ANNOTATION_TYPE_KEY] == KWARGS_ANNOTATION_TYPE_VALUE_DEFINITION):
            annotation_worklogs = AnnotationWorklog.objects\
                .filter(concept_defined__concept__id=self.kwargs[KWARGS_CONCEPT_ID_KEY])\
                .filter(concept_defined__document__id=self.kwargs[KWARGS_DOCUMENT_ID_KEY])
        serializer = AnnotationWorklogSerializer(annotation_worklogs, many=True)
        rows = []
        for data_item in serializer.data:
            print(data_item['user'])
            concept_offset_base = None
            if (data_item['concept_occurs']):
                concept_offset_base = ConceptOccurs.objects.get(pk=data_item['concept_occurs'])
            elif (data_item['concept_defined']):
                concept_offset_base = ConceptDefined.objects.get(pk=data_item['concept_defined'])
            if concept_offset_base:
                row = {}
                row['id'] = str(data_item['id'])
                row['quote'] = concept_offset_base.quote
                row['ranges'] = []
                ranges_dict = {}
                ranges_dict['start'] = str(concept_offset_base.start)
                ranges_dict['startOffset'] = concept_offset_base.startOffset
                ranges_dict['end'] = str(concept_offset_base.end)
                ranges_dict['endOffset'] = concept_offset_base.endOffset
                row['ranges'].append(ranges_dict)
                row['text'] = ''
                rows.append(row)

        response = {}
        response['total'] = str(len(rows))
        response['rows'] = rows
        return Response(response)

class CreateListAPIView(ListCreateAPIView):
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()

    def post(self, request, *args, **kwargs):
        concept_offset_data = request.data
        concept_offset_data.update({'concept': str(self.kwargs['concept_id'])})
        concept_offset_data.update({'document': str(self.kwargs['document_id'])})
        concept_offset_data.update({'quote': str(request.data['quote']).replace('"', '\\\"')})
        concept_offset_data.update({'probability': 1.0})
        concept_offset_data.update({'start': request.data['ranges'][0]['start']})
        concept_offset_data.update({'startOffset': request.data['ranges'][0]['startOffset']})
        concept_offset_data.update({'end': request.data['ranges'][0]['end']})
        concept_offset_data.update({'endOffset': request.data['ranges'][0]['endOffset']})

        annotation_worklog_data = request.data
        annotation_worklog_data.update({'user': request.user.id})
        annotation_worklog_data.update({'created_at': datetime.datetime.now()})
        annotation_worklog_data.update({'updated_at': datetime.datetime.now()})
        annotation_worklog_data.update({'document': str(self.kwargs['document_id'])})

        concept_occurs = None
        concept_defined = None
        if (self.kwargs[KWARGS_ANNOTATION_TYPE_KEY] == KWARGS_ANNOTATION_TYPE_VALUE_OCCURENCE):
            concept_occurs_serializer = ConceptOccursSerializer(data=concept_offset_data)
            if concept_occurs_serializer.is_valid():
                concept_occurs = concept_occurs_serializer.save()
                annotation_worklog_data.update({'concept_occurs': concept_occurs.id})
                annotation_worklog_data.update({'concept_defined': None})
            else:
                return Response(concept_occurs_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif (self.kwargs[KWARGS_ANNOTATION_TYPE_KEY] == KWARGS_ANNOTATION_TYPE_VALUE_DEFINITION):
            concept_defined_serializer = ConceptDefinedSerializer(data=concept_offset_data)
            if concept_defined_serializer.is_valid():
                concept_defined = concept_defined_serializer.save()
                annotation_worklog_data.update({'concept_occurs': None})
                annotation_worklog_data.update({'concept_defined': concept_defined.id})
            else:
                return Response(concept_defined_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        annotation_worklog_serializer = AnnotationWorklogSerializer(data=annotation_worklog_data)
        if annotation_worklog_serializer.is_valid():
            annotation_worklog = annotation_worklog_serializer.save()
            annotation_worklog_serializer = AnnotationWorklogSerializer(annotation_worklog)
            return Response(annotation_worklog_serializer.data, status=status.HTTP_201_CREATED)
        return Response(annotation_worklog_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAPIView(APIView):
    def delete(self, request, annotation_type, concept_id, document_id, annotation_id, format=None):
        annotation_worklog = AnnotationWorklog.objects.get(id=annotation_id)
        annotation_worklog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

