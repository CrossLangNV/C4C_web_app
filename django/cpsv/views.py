import os

from django.shortcuts import render

# Create your views here.
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from searchapp.models import Document

from cpsv.cpsv_rdf_call import get_contact_points, get_public_services, get_contact_point_info

import logging as logger

from cpsv.models import PublicService

from cpsv.serializers import PublicServiceObligationSerializer

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


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 1000


class RdfContactPointsAPIView(APIView, PaginationHandlerMixin):
    queryset = Document.objects.none()

    def get(self, request, format=None):
        cp_ids = get_contact_points(RDF_FUSEKI_URL)

        contact_points = []
        for cpid in cp_ids:
            # logger.info(cpid[0])
            contact_points.append(get_contact_point_info(RDF_FUSEKI_URL, cpid[0]))
            # logger.info(get_contact_point_info(RDF_FUSEKI_URL, cpid[0]))

        return Response(contact_points)


class RdfPublicServicesAPIView(APIView, PaginationHandlerMixin):
    pagination_class = SmallResultsSetPagination
    queryset = PublicService.objects.all()
    serializer_class = PublicServiceObligationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']

    def post(self, request, format=None, *args, **kwargs):
        q = PublicService.objects.all()
        rdf_results = get_public_services(RDF_FUSEKI_URL)
        logger.info("rdf_results: %s", rdf_results)

        uris = [item[0] for item in rdf_results]
        logger.info("uris: %s", uris)


        if rdf_results:
            q = q.filter(identifier__in=rdf_results)

        else:
            q = PublicService.objects.none()

        page = self.paginate_queryset(q)

        serializer = self.get_paginated_response(
            self.serializer_class(page, many=True, context={'request': request}).data)

        return Response(serializer.data)


