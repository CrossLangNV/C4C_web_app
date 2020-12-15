from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from glossary.models import AcceptanceState, AcceptanceStateValue, Comment, Concept, Tag, AnnotationWorklog, ConceptOccurs, ConceptDefined
from glossary.serializers import AcceptanceStateSerializer, ConceptSerializer, TagSerializer, \
    AnnotationWorklogSerializer, ConceptOccursSerializer, ConceptDefinedSerializer
from searchapp.models import Document
from searchapp.serializers import DocumentSerializer
from glossary.serializers import CommentSerializer
from searchapp.solr_call import solr_search_paginated
from searchapp.permissions import IsOwner, IsOwnerOrSuperUser
from django.db.models import Q

from pprint import pprint

import status
import datetime
import json

class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConceptListAPIView(ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'acceptance_state_max_probability']

    def get_queryset(self):
        # TODO Remove the Unknown term and empty definition exclude filter
        q = Concept.objects.all().exclude(name__exact='Unknown').exclude(definition__exact='')
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
        return q.order_by("name")


class ConceptDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
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
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    

class WorkLogAPIView(ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()


class WorklogDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
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

# Terms and Definitions Annotations API

class RootAPIView(APIView):
    def get(self, request, annotation_type, concept_id, document_id, format=None):
        annotation_store_metadata = '{"message": "Annotator Store API","links": {}}'
        return Response(annotation_store_metadata)

class SearchListAPIView(ListCreateAPIView):
    # serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = AnnotationWorklog.objects.all()
        serializer = AnnotationWorklogSerializer(queryset, many=True)
        count = 0
        rows_data = ''
        for data_item in serializer.data:
            concept_offset_base = None
            if (self.kwargs['annotation_type'] == "occurence"):
                try:
                    concept_offset_base = ConceptOccurs.objects.get(pk=data_item["concept_occurs"])
                except ConceptOccurs.DoesNotExist:
                    continue
            elif (self.kwargs['annotation_type'] == "definition"):
                try:
                    concept_offset_base = ConceptDefined.objects.get(pk=data_item["concept_defined"])
                except ConceptDefined.DoesNotExist:
                    continue
            if concept_offset_base and concept_offset_base.id:
                if concept_offset_base.concept:
                    print(3)
                    print(concept_offset_base.concept.id)
                    print(self.kwargs['concept_id'])
                    if (str(concept_offset_base.concept.id) == self.kwargs['concept_id']):
                        print(4)
                        if (str(concept_offset_base.document.id) == self.kwargs['document_id']):
                            print(5)
                            count += 1
                            if count != 1:
                                rows_data += ','
                            rows_data += '{'
                            rows_data += '"id":"' + str(data_item["id"]) + '",'
                            rows_data += '"quote":"' + concept_offset_base.quote + '",'
                            rows_data += '"ranges":[{'
                            rows_data += '"start":"' + str(concept_offset_base.start) + '",'
                            rows_data += '"startOffset":' + str(concept_offset_base.startOffset) + ','
                            rows_data += '"end":"' + str(concept_offset_base.end) + '",'
                            rows_data += '"endOffset":' + str(concept_offset_base.endOffset)
                            rows_data += '}],'
                            rows_data += '"text":""'
                            rows_data += '}'

        response_string = '{"total":' + str(count) +',"rows":[' + rows_data + ']}'
        return Response(json.loads(response_string))

class CreateListAPIView(ListCreateAPIView):
    # TODO: these might be removed
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()

    def post(self, request, *args, **kwargs):
        concept_offset_data = request.data
        concept_offset_data.update({'concept': str(self.kwargs['concept_id'])})
        concept_offset_data.update({'document': str(self.kwargs['document_id'])})
        quote_with_escaped_double_quotes = str(request.data['quote']).replace('"', '\\\"')
        concept_offset_data.update({'quote': quote_with_escaped_double_quotes})
        concept_offset_data.update({'probability': 1.0})
        concept_offset_data.update({'start': request.data['ranges'][0]['start']})
        concept_offset_data.update({'startOffset': request.data['ranges'][0]['startOffset']})
        concept_offset_data.update({'end': request.data['ranges'][0]['end']})
        concept_offset_data.update({'endOffset': request.data['ranges'][0]['endOffset']})

        annotation_worklog_data = request.data
        # works?
        annotation_worklog_data.update({'user': request.user.id})
        annotation_worklog_data.update({'created_at': datetime.datetime.now()})
        annotation_worklog_data.update({'updated_at': datetime.datetime.now()})

        if (self.kwargs['annotation_type'] == "occurence"):
            concept_occurs_serializer = ConceptOccursSerializer(data=concept_offset_data)
            if concept_occurs_serializer.is_valid():
                concept_occurs = concept_occurs_serializer.save()
                pprint(vars(concept_occurs))
                
                annotation_worklog_serializer = AnnotationWorklogSerializer(data=annotation_worklog_data)
                annotation_worklog_data.update({'concept_occurs': concept_occurs.id})
                annotation_worklog_data.update({'concept_defined': None})
                if annotation_worklog_serializer.is_valid():
                    annotation_worklog = annotation_worklog_serializer.save()
                    annotation_worklog_serializer = AnnotationWorklogSerializer(annotation_worklog)
                    # or should i return the other serializer's response?
                    return Response(annotation_worklog_serializer.data, status=status.HTTP_201_CREATED)
                return Response(annotation_worklog_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(concept_occurs_serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        elif (self.kwargs['annotation_type'] == "definition"):
            concept_defined_serializer = ConceptDefinedSerializer(data=concept_offset_data)
            if concept_defined_serializer.is_valid():
                concept_defined = concept_defined_serializer.save()
                concept_defined_serializer = ConceptDefinedSerializer(concept_defined)
                
                # possibly, you could put this part outside of the if (so once for O & D together)
                annotation_worklog_serializer = AnnotationWorklogSerializer(data=annotation_worklog_data)
                annotation_worklog_data.update({'concept_occurs': None})
                annotation_worklog_data.update({'concept_defined': concept_defined.id})
                if annotation_worklog_serializer.is_valid():
                    annotation_worklog = annotation_worklog_serializer.save()
                    annotation_worklog_serializer = AnnotationWorklogSerializer(annotation_worklog)
                    # or should i return the other serializer's response?
                    return Response(annotation_worklog_serializer.data, status=status.HTTP_201_CREATED)
                return Response(annotation_worklog_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(concept_occurs_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # if possible, put another 400 here (by creating serializer in the beginning, and using save)

class DeleteAPIView(APIView):
    def delete(self, request, annotation_type, concept_id, document_id, annotation_id, format=None):
        annotation = AnnotationWorklog.objects.get(id=annotation_id)
        annotation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

