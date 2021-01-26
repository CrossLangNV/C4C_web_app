import os

from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from searchapp.models import Document

from cpsv.cpsv_rdf_call import get_contact_points, get_public_services

RDF_FUSEKI_URL = os.environ['RDF_FUSEKI_URL']


class RdfContactPointsAPIView(APIView):
    queryset = Document.objects.none()

    def get(self, request, format=None):
        result = get_contact_points(RDF_FUSEKI_URL)
        return Response(result)


class RdfPublicServicesAPIView(APIView):
    queryset = Document.objects.none()

    def get(self, request, format=None):
        result = get_public_services(RDF_FUSEKI_URL)
        return Response(result)
