import os

from django.shortcuts import render

# Create your views here.
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from searchapp.models import Document

from cpsv.cpsv_rdf_call import get_contact_points, get_public_services, get_contact_point_info

import logging as logger

from cpsv.models import PublicService,ContactPoint

from cpsv.serializers import PublicServiceSerializer, ContactPointSerializer

RDF_FUSEKI_URL = os.environ['RDF_FUSEKI_URL']


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


class SmallResultsSetPagination(LimitOffsetPagination):
    default_limit = 5
    limit_query_param = 'rows'
    offset_query_param = 'page'


class RdfContactPointsAPIView(APIView, PaginationHandlerMixin):
    pagination_class = SmallResultsSetPagination
    queryset = ContactPoint.objects.all()
    serializer_class = ContactPointSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['description']

    def post(self, request, format=None, *args, **kwargs):
        q = ContactPoint.objects.all()
        keyword = self.request.GET.get('keyword', "")

        cp_ids = get_contact_points(RDF_FUSEKI_URL)
        rdf_uris = [str(item['uri']) for item in cp_ids]
        logger.info("rdf_uris: %s", rdf_uris)

        if rdf_uris:
            q = q.filter(identifier__in=rdf_uris)
            if keyword:
                q = q.filter(name__icontains=keyword)
        else:
            q = ContactPoint.objects.none()

        page = self.paginate_queryset(q)

        serializer = self.get_paginated_response(
            self.serializer_class(page, many=True, context={'request': request}).data)

        logger.info("serializer.data: %s", serializer.data)

        return Response(serializer.data)


class RdfPublicServicesAPIView(APIView, PaginationHandlerMixin):
    pagination_class = SmallResultsSetPagination
    queryset = PublicService.objects.all()
    serializer_class = PublicServiceSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']

    def post(self, request, format=None, *args, **kwargs):
        q = PublicService.objects.all()
        keyword = self.request.GET.get('keyword', "")
        website = self.request.GET.get('website', "")

        rdf_results = get_public_services(RDF_FUSEKI_URL)

        rdf_uris = [str(item['uri']) for item in rdf_results]

        if rdf_uris:
            q = q.filter(identifier__in=rdf_uris)
            if keyword:
                q = q.filter(name__icontains=keyword)
            if website:
                q = q.filter(website__name__iexact=website)

        else:
            q = PublicService.objects.none()

        page = self.paginate_queryset(q)

        serializer = self.get_paginated_response(
            self.serializer_class(page, many=True, context={'request': request}).data)

        logger.info("serializer.data: %s", serializer.data)

        return Response(serializer.data)


