import os

from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from searchapp.models import Document

from cpsv.cpsv_rdf_call import get_contact_points, get_public_services, get_contact_point_info

import logging as logger

RDF_FUSEKI_URL = os.environ['RDF_FUSEKI_URL']


class RdfContactPointsAPIView(APIView):
    queryset = Document.objects.none()

    def get(self, request, format=None):
        cp_ids = get_contact_points(RDF_FUSEKI_URL)

        contact_points = []
        for cpid in cp_ids:
            # logger.info(cpid[0])
            contact_points.append(get_contact_point_info(RDF_FUSEKI_URL, cpid[0]))
            # logger.info(get_contact_point_info(RDF_FUSEKI_URL, cpid[0]))

        return Response(contact_points)


class RdfPublicServicesAPIView(APIView):
    queryset = Document.objects.none()

    def get(self, request, format=None):
        result = get_public_services(RDF_FUSEKI_URL)
        return Response(result)
