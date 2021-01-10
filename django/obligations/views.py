from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from obligations.models import ReportingObligation, AcceptanceState, AcceptanceStateValue, Comment, Tag, ROAnnotationWorklog, ReportingObligationOffsets
from obligations.serializers import ReportingObligationSerializer, AcceptanceStateSerializer, CommentSerializer,\
    TagSerializer, ROAnnotationWorklogSerializer, ReportingObligationOffsetsSerializer
from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
import logging as logger

from .rdf_call import rdf_get_available_entities, rdf_get_predicate, \
    rdf_get_all_reporting_obligations, rdf_query_predicate_single, rdf_query_predicate_multiple, \
    rdf_query_predicate_multiple_id, rdf_get_name_of_entity
from searchapp.permissions import IsOwner, IsOwnerOrSuperUser

import json
import datetime
import status

# Annotation API consants

ANNOTATION_STORE_METADATA = '{"message": "Annotator Store API","links": {}}'
KWARGS_RO_ID_KEY = 'ro_id'
KWARGS_DOCUMENT_ID_KEY = 'document_id'

class PaginationHandlerMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 1000


# For multiple RDF queries
class ReportingObligationQueryMultipleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination

    def post(self, request, format=None):
        filter_list = request.data['filters']

        filter_list_tuple = [(d['pred'], d['value']) for d in filter_list]

        result = rdf_query_predicate_multiple_id(filter_list_tuple)

        return Response(result)


# This one is used to fill the dropdowns in the UI
class ReportingObligationEntityMapAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination

    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_cookie)
    def get(self, request, format=None):

        all_entities = rdf_get_available_entities()
        arr = []

        for entity in all_entities:

            # TODO: Currently not supporting "Entity" in RDF
            if not "Entity" in rdf_get_name_of_entity(entity):

                entity_name = rdf_get_name_of_entity(entity)
                options = [{"name": entity_name, "code": ""}]
                for option in sorted(rdf_get_predicate(entity)):
                    options.append({"name": option, "code": option})
                item = {"entity": entity, "options": options}
                arr.append(item)

        arr.sort(key=lambda x: x['options'][0]['name'])

        arr_whowhatwhen = [None for _ in range(5)]

        l_entities = ["http://dgfisma.com/reporting_obligations/hasReporter",
                      "http://dgfisma.com/reporting_obligations/hasPropMod",
                      "http://dgfisma.com/reporting_obligations/hasVerb",
                      "http://dgfisma.com/reporting_obligations/hasReport",
                      "http://dgfisma.com/reporting_obligations/hasRegulatoryBody",
                      "http://dgfisma.com/reporting_obligations/hasPropTmp"
                      ]

        arr_whowhatwhen = []
        for s_ent in l_entities:
            for filter in arr:
                if filter['entity'] == s_ent:
                    arr_whowhatwhen.append(arr.pop(arr.index(filter)))
                    break

        arr = arr_whowhatwhen + arr

        return Response(arr)


class ReportingObligationListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination
    queryset = ReportingObligation.objects.all()
    serializer_class = ReportingObligationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']

    def get_queryset(self):
        q = ReportingObligation.objects.all()
        keyword = self.request.GET.get('keyword', "")
        if keyword:
            q = q.filter(name__icontains=keyword)

        return q.order_by("name")


# Query for RO+RDF ROS search
class ReportingObligationListRdfQueriesAPIView(APIView, PaginationHandlerMixin):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination
    queryset = ReportingObligation.objects.all()
    serializer_class = ReportingObligationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']

    def post(self, request, format=None, *args, **kwargs):
        request.data['user'] = request.user.id

        q = ReportingObligation.objects.all()
        rdf_filters = request.data['rdfFilters']
        rdf_results = rdf_query_predicate_multiple_id(rdf_filters.items())

        if rdf_results:
            q = q.filter(rdf_id__in=rdf_results)
        else:
            q = ReportingObligation.objects.none()

        page = self.paginate_queryset(q)

        serializer = self.get_paginated_response(self.serializer_class(page, many=True, context={'request': request}).data)

        return Response(serializer.data)




class ReportingObligationDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ReportingObligation.objects.all()
    serializer_class = ReportingObligationSerializer


# Entities
class ReportingObligationAvailableEntitiesAPIView(APIView):

    def get(self, request, format=None):
        result = rdf_get_available_entities()
        return Response(result)


# Predicate
class ReportingObligationGetByPredicate(APIView):

    def post(self, request, format=None):
        predicate = request.data['predicate']
        result = rdf_get_predicate(predicate)
        return Response(result)


# Get all RO's from RDF
class ReportingObligationsRDFListAPIView(APIView):

    def get(self, request, format=None):
        result = rdf_get_all_reporting_obligations()
        return Response(result)


class TagListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


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

# RO Annotations API

class RootAPIView(APIView):
    def get(self, request, subject_id, document_id, format=None):
        return Response(ANNOTATION_STORE_METADATA)

class SearchListAPIView(ListCreateAPIView):
    serializer_class = ROAnnotationWorklogSerializer

    def list(self, request, *args, **kwargs):
        annotation_worklogs = ROAnnotationWorklog.objects\
            .filter(ro_offsets__ro__id=self.kwargs[KWARGS_RO_ID_KEY])\
            .filter(ro_offsets__document__id=self.kwargs[KWARGS_DOCUMENT_ID_KEY])
        serializer = ROAnnotationWorklogSerializer(annotation_worklogs, many=True)
        rows = []
        for data_item in serializer.data:
            ro_offsets = ReportingObligationOffsets.objects.get(pk=data_item['ro_offsets'])
            if ro_offsets:
                row = {}
                row['id'] = str(data_item['id'])
                row['quote'] = ro_offsets.quote
                row['ranges'] = []
                ranges_dict = {}
                ranges_dict['start'] = str(ro_offsets.start)
                ranges_dict['startOffset'] = ro_offsets.startOffset
                ranges_dict['end'] = str(ro_offsets.end)
                ranges_dict['endOffset'] = ro_offsets.endOffset
                row['ranges'].append(ranges_dict)
                row['text'] = ''
                rows.append(row)

        response = {}
        response['total'] = str(len(rows))
        response['rows'] = rows
        print(response)
        return Response(response)

class CreateListAPIView(ListCreateAPIView):
    serializer_class = ROAnnotationWorklogSerializer

    def post(self, request, *args, **kwargs):
        ro_offsets_data = request.data
        ro_offsets_data.update({'ro': str(self.kwargs[KWARGS_RO_ID_KEY])})
        ro_offsets_data.update({'document': str(self.kwargs[KWARGS_DOCUMENT_ID_KEY])})
        ro_offsets_data.update({'quote': str(request.data['quote']).replace('"', '\\\"')})
        ro_offsets_data.update({'probability': 1.0})
        ro_offsets_data.update({'start': request.data['ranges'][0]['start']})
        ro_offsets_data.update({'startOffset': request.data['ranges'][0]['startOffset']})
        ro_offsets_data.update({'end': request.data['ranges'][0]['end']})
        ro_offsets_data.update({'endOffset': request.data['ranges'][0]['endOffset']})

        annotation_worklog_data = request.data
        annotation_worklog_data.update({'user': request.user.id})
        annotation_worklog_data.update({'created_at': datetime.datetime.now()})
        annotation_worklog_data.update({'updated_at': datetime.datetime.now()})

        ro_offsets_serializer = ReportingObligationOffsetsSerializer(data=ro_offsets_data)
        if ro_offsets_serializer.is_valid():
            ro_offsets = ro_offsets_serializer.save()
            annotation_worklog_data.update({'ro_offsets': ro_offsets.id})
        else:
            return Response(ro_offsets_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        annotation_worklog_serializer = ROAnnotationWorklogSerializer(data=annotation_worklog_data)
        if annotation_worklog_serializer.is_valid():
            annotation_worklog = annotation_worklog_serializer.save()
            annotation_worklog_serializer = ROAnnotationWorklogSerializer(annotation_worklog)
            return Response(annotation_worklog_serializer.data, status=status.HTTP_201_CREATED)
        return Response(annotation_worklog_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAPIView(APIView):
    def delete(self, request, ro_id, document_id, annotation_id, format=None):
        annotation_worklog = ROAnnotationWorklog.objects.get(id=annotation_id)
        annotation_worklog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

