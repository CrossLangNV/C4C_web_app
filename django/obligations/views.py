from obligations.models import ReportingObligation
from obligations.serializers import ReportingObligationSerializer
from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView


from .rdf_call import rdf_get_verbs, rdf_get_reporters, rdf_get_reports, rdf_get_regulatory_body, rdf_get_propmod, rdf_get_entity, rdf_get_frequency


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ReportingObligationListAPIView(ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]
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
    

class ReportingObligationDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    queryset = ReportingObligation.objects.all()
    serializer_class = ReportingObligationSerializer


# Reporters from RDF
class ReportingObligationReportersListAPIView(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_reporters()
        return Response(result)


class ReportingObligationVerbsListAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_verbs()
        return Response(result)


class ReportingObligationReportsListAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_reports()
        return Response(result)


class ReportingObligationRegulatoryBodyListAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_regulatory_body()
        return Response(result)


class ReportingObligationPropModListAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_propmod()
        return Response(result)


class ReportingObligationEntityListAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_entity()
        return Response(result)


class ReportingObligationFrequencyListAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        result = rdf_get_frequency()
        return Response(result)

