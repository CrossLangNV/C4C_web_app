import os

from django.shortcuts import render

# Create your views here.
from rest_framework import filters, permissions
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from cpsv.rdf_call import get_dropdown_options
from searchapp.models import Document

from cpsv.cpsv_rdf_call import get_contact_points, get_public_services, get_contact_point_info
from cpsv.rdf_call import get_public_service_uris_filter

import logging as logger

from cpsv.models import PublicService, ContactPoint

from cpsv.serializers import PublicServiceSerializer, ContactPointSerializer

RDF_FUSEKI_URL = os.environ["RDF_FUSEKI_URL"]


class PaginationHandlerMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, "_paginator"):
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
    limit_query_param = "rows"
    offset_query_param = "page"


class RdfContactPointsAPIView(APIView, PaginationHandlerMixin):
    pagination_class = SmallResultsSetPagination
    queryset = ContactPoint.objects.all()
    serializer_class = ContactPointSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["description"]

    def post(self, request, format=None, *args, **kwargs):
        q = ContactPoint.objects.all()
        keyword = self.request.GET.get("keyword", "")

        cp_ids = get_contact_points(RDF_FUSEKI_URL)
        rdf_uris = [str(item["uri"]) for item in cp_ids]
        logger.info("rdf_uris: %s", rdf_uris)

        if rdf_uris:
            q = q.filter(identifier__in=rdf_uris)
            if keyword:
                q = q.filter(name__icontains=keyword)
        else:
            q = ContactPoint.objects.none()

        page = self.paginate_queryset(q)

        serializer = self.get_paginated_response(
            self.serializer_class(page, many=True, context={"request": request}).data
        )

        return Response(serializer.data)


class RdfPublicServicesAPIView(APIView, PaginationHandlerMixin):
    pagination_class = SmallResultsSetPagination
    queryset = PublicService.objects.all()
    serializer_class = PublicServiceSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["name"]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, *args, **kwargs):
        q = PublicService.objects.all()
        keyword = self.request.GET.get("keyword", "")
        website = self.request.GET.get("website", "")

        dict_rdf_filters = request.data["rdfFilters"]
        logger.info("dict_rdf_filters: %s", dict_rdf_filters)

        # rdf_results = get_public_services(RDF_FUSEKI_URL)
        #        rdf_uris = [str(item["uri"]) for item in rdf_results]

        rdf_uris = get_public_service_uris_filter(
            filter_concepts=dict_rdf_filters.get('http://purl.org/vocab/cpsv#isClassifiedBy'),
            filter_public_organization=dict_rdf_filters.get("http://data.europa.eu/m8g/hasCompetentAuthority"),
            filter_contact_point=dict_rdf_filters.get("http://www.w3.org/ns/dcat#hasContactPoint")
        )
        logger.info("rdf_uris: %s", rdf_uris)

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
            self.serializer_class(page, many=True, context={"request": request}).data
        )

        return Response(serializer.data)


class PublicServiceDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = PublicService.objects.all()
    serializer_class = PublicServiceSerializer


class ContactPointDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = ContactPoint.objects.all()
    serializer_class = ContactPointSerializer


class PublicServicesEntityOptionsAPIView(APIView):
    queryset = PublicService.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        mock_data = [
            "http://www.w3.org/ns/dcat#hasContactPoint",
            "http://data.europa.eu/m8g/hasCompetentAuthority",
            "http://purl.org/vocab/cpsv#isClassifiedBy",
            "http://cefat4cities.com/public_services/hasBusinessEvent",
            "http://cefat4cities.com/public_services/hasLifeEvent",
        ]

        return Response(mock_data)


class DropdownOptionsAPIView(APIView):
    queryset = PublicService.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, *args, **kwargs):
        uri_type_has = request.data["uri_type"]
        keyword = request.data["keyword"]
        dict_rdf_filters = request.data["rdfFilters"]

        values = get_dropdown_options(uri_type_has)

        # logger.info("values: %s", values)

        # result = [{"name": a} for a in values]

        return Response(values)
