from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from obligations.models import ReportingObligation, AcceptanceState, AcceptanceStateValue, Comment, Tag
from obligations.serializers import ReportingObligationSerializer, AcceptanceStateSerializer, CommentSerializer,\
    TagSerializer
from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
import logging as logger
import os
from minio import Minio
from minio.error import NoSuchKey

from .rdf_call import rdf_get_available_entities, rdf_get_predicate, \
    rdf_get_all_reporting_obligations, rdf_query_predicate_single, rdf_query_predicate_multiple, \
    rdf_query_predicate_multiple_id, rdf_get_name_of_entity
from searchapp.permissions import IsOwner, IsOwnerOrSuperUser


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


class ReportingObligationDocumentHtmlAPIView(APIView):
    #permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperUser]

    def get(self, request, document_id, format=None):

        minio_client = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                             secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
        bucket_name = "ro-html-output"

        EXTRACT_RO_NLP_VERSION = os.environ.get(
            'EXTRACT_RO_NLP_VERSION', 'd16bba97890')

        try:
            html_file = minio_client.get_object(bucket_name, document_id + "-" + EXTRACT_RO_NLP_VERSION + ".html")
            result = html_file.data

            logger.info(result)
            return Response(result, HTTP_200_OK)
        except NoSuchKey as err:
            return Response("", HTTP_204_NO_CONTENT)
