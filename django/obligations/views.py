from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from obligations.models import ReportingObligation, AcceptanceState, AcceptanceStateValue, Comment, Tag
from obligations.serializers import ReportingObligationSerializer, AcceptanceStateSerializer, CommentSerializer, \
    TagSerializer
from searchapp.permissions import IsOwner, IsOwnerOrSuperUser
from .rdf_call import rdf_get_available_entities, rdf_get_predicate, \
    rdf_get_all_reporting_obligations, rdf_query_predicate_multiple_id, rdf_get_name_of_entity


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
    pagination_class = SmallResultsSetPagination
    queryset = ReportingObligation.objects.none()

    def post(self, request, format=None):
        filter_list = request.data['filters']

        filter_list_tuple = [(d['pred'], d['value']) for d in filter_list]

        result = rdf_query_predicate_multiple_id(filter_list_tuple)

        return Response(result)


# This one is used to fill the dropdowns in the UI
class ReportingObligationEntityMapAPIView(APIView):
    pagination_class = SmallResultsSetPagination
    queryset = ReportingObligation.objects.none()

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
    pagination_class = SmallResultsSetPagination
    queryset = ReportingObligation.objects.all()
    serializer_class = ReportingObligationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']

    def get_queryset(self):
        groups = self.request.user.groups.all()
        opinion = any(group.name == 'opinion' for group in groups)

        q = ReportingObligation.objects.all()
        keyword = self.request.GET.get('keyword', "")
        if keyword:
            q = q.filter(name__icontains=keyword)

        if opinion:
            rejected_state_ids = AcceptanceState.objects.filter(
                Q(user__groups__name='decision') & Q(value="Rejected")).values_list('id', flat=True)
            q = q.exclude(Q(acceptance_states__in=list(rejected_state_ids)))
        return q.order_by("name")


# Query for RO+RDF ROS search
class ReportingObligationListRdfQueriesAPIView(APIView, PaginationHandlerMixin):
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
    queryset = ReportingObligation.objects.all()
    serializer_class = ReportingObligationSerializer


# Entities
class ReportingObligationAvailableEntitiesAPIView(APIView):
    queryset = ReportingObligation.objects.none()

    def get(self, request, format=None):
        result = rdf_get_available_entities()
        return Response(result)


# Predicate
class ReportingObligationGetByPredicate(APIView):
    queryset = ReportingObligation.objects.none()

    def post(self, request, format=None):
        predicate = request.data['predicate']
        result = rdf_get_predicate(predicate)
        return Response(result)


# Get all RO's from RDF
class ReportingObligationsRDFListAPIView(APIView):
    queryset = ReportingObligation.objects.none()

    def get(self, request, format=None):
        result = rdf_get_all_reporting_obligations()
        return Response(result)


class TagListAPIView(ListCreateAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class AcceptanceStateValueAPIView(APIView):
    queryset = AcceptanceState.objects.none()

    def get(self, request, format=None):
        return Response([state.value for state in AcceptanceStateValue])


class AcceptanceStateListAPIView(ListCreateAPIView):
    serializer_class = AcceptanceStateSerializer
    queryset = AcceptanceState.objects.none()

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
