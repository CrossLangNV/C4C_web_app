from obligations.models import ReportingObligation
from obligations.serializers import ReportingObligationSerializer
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination


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

