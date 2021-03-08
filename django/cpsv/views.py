import abc
import logging as logger
import os

# Create your views here.
import requests
from rest_framework import filters, permissions
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from cpsv.cpsv_rdf_call import get_contact_points
from cpsv.models import PublicService, ContactPoint
from cpsv.rdf_call import (
    get_dropdown_options_for_public_services,
    get_dropdown_options_for_contact_points,
    get_contact_point_uris_filter,
)
from cpsv.rdf_call import get_public_service_uris_filter
from cpsv.serializers import PublicServiceSerializer, ContactPointSerializer

RDF_FUSEKI_URL = os.environ["RDF_FUSEKI_URL"]
URI_IS_CLASSIFIED_BY = os.environ["URI_IS_CLASSIFIED_BY"]
URI_HAS_COMPETENT_AUTHORITY = os.environ["URI_HAS_COMPETENT_AUTHORITY"]
URI_HAS_CONTACT_POINT = os.environ["URI_HAS_CONTACT_POINT"]


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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, *args, **kwargs):
        q = ContactPoint.objects.all()
        keyword = self.request.GET.get("keyword", "")

        dict_rdf_filters = request.data["rdfFilters"]
        logger.info("dict_rdf_filters: %s", dict_rdf_filters)

        rdf_uris = get_contact_point_uris_filter(filter_public_service=dict_rdf_filters.get(URI_HAS_CONTACT_POINT))
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
            filter_concepts=dict_rdf_filters.get(URI_IS_CLASSIFIED_BY),
            filter_public_organization=dict_rdf_filters.get(URI_HAS_COMPETENT_AUTHORITY),
            filter_contact_point=dict_rdf_filters.get(URI_HAS_CONTACT_POINT),
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


class EntityOptionsAPIView(APIView, abc.ABC):
    queryset = PublicService.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        mock_data = self.get_mock_data()

        return Response(mock_data)

    @staticmethod
    @abc.abstractmethod
    def get_mock_data():
        pass


class PublicServicesEntityOptionsAPIView(EntityOptionsAPIView):
    @staticmethod
    def get_mock_data():
        mock_data = [
            URI_HAS_CONTACT_POINT,
            URI_HAS_COMPETENT_AUTHORITY,
            URI_IS_CLASSIFIED_BY,
            "http://cefat4cities.com/public_services/hasBusinessEvent",
            "http://cefat4cities.com/public_services/hasLifeEvent",
        ]

        return mock_data


class ContactPointsEntityOptionsAPIView(EntityOptionsAPIView):
    @staticmethod
    def get_mock_data():
        mock_data = [
            URI_HAS_CONTACT_POINT,
        ]

        return mock_data


class DropdownOptionsAPIView(APIView, abc.ABC):
    queryset = PublicService.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None, *args, **kwargs):
        uri_type_has = request.data["uri_type"]
        keyword = request.data["keyword"]
        dict_rdf_filters = request.data["rdfFilters"]

        values = self.get_values(uri_type_has)

        return Response(values)

    @staticmethod
    @abc.abstractmethod
    def get_values(uri_type_has):
        pass


class DropdownOptionsPublicServicesAPIView(DropdownOptionsAPIView):
    @staticmethod
    def get_values(uri_type_has):
        values = get_dropdown_options_for_public_services(uri_type_has)
        return values


class DropdownOptionsContactPointsAPIView(DropdownOptionsAPIView):
    @staticmethod
    def get_values(uri_type_has):
        values = get_dropdown_options_for_contact_points(uri_type_has)
        return values


class FusekiDatasetAPIView(APIView):
    queryset = PublicService.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        r = requests.get(RDF_FUSEKI_URL)
        return Response(r.content)
