from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from obligations.models import ReportingObligation
from obligations.serializers import ReportingObligationSerializer
from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
import logging as logger

from .rdf_call import rdf_get_available_entities, rdf_get_predicate, \
    rdf_get_all_reporting_obligations, rdf_query_predicate_single, rdf_query_predicate_multiple, \
    rdf_query_predicate_multiple_id, rdf_get_name_of_entity


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

        # rdf_get_predicate(predicate)
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
        q = ReportingObligation.objects.all()
        rdf_filters = request.data['rdfFilters']

        rdf_results = rdf_query_predicate_multiple_id(rdf_filters.items())

        if rdf_results:
            q = q.filter(rdf_id__in=rdf_results)
        else:
            q = ReportingObligation.objects.none()

        page = self.paginate_queryset(q)
        if page is not None:
            serializer = self.get_paginated_response(self.serializer_class(page, many=True).data)
        else:
            serializer = self.serializer_class(q, many=True)

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


