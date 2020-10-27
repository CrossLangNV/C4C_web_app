from rest_framework import permissions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from glossary.models import AcceptanceState, AcceptanceStateValue, Comment, Concept, Tag, AnnotationWorklog
from glossary.serializers import AcceptanceStateSerializer, ConceptSerializer, TagSerializer, \
    AnnotationWorklogSerializer
from searchapp.models import Document
from searchapp.serializers import DocumentSerializer
from glossary.serializers import CommentSerializer
from searchapp.solr_call import solr_search_paginated
from searchapp.permissions import IsOwner, IsOwnerOrSuperUser
from django.db.models import Q

class SmallResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConceptListAPIView(ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'acceptance_state_max_probability']

    def get_queryset(self):
        # TODO Remove the Unknown term and empty definition exclude filter
        q = Concept.objects.all().exclude(name__exact='Unknown').exclude(definition__exact='')
        keyword = self.request.GET.get('keyword', "")
        if keyword:
            q = q.filter(name__icontains=keyword)
        showonlyown = self.request.GET.get('showOnlyOwn', "")
        if showonlyown == "true":
            email = self.request.GET.get('email', "")
            q = q.filter(Q(acceptance_states__user__email=email) & (Q(acceptance_states__value="Accepted") |
                                                                    Q(acceptance_states__value="Rejected")))
        filtertype = self.request.GET.get('filterType', "")
        if filtertype == "unvalidated":
            q = q.exclude(Q(acceptance_states__value="Rejected")
                          | Q(acceptance_states__value="Accepted"))
        if filtertype == "accepted":
            q = q.filter(acceptance_states__value="Accepted").distinct()
        if filtertype == "rejected":
            q = q.filter(acceptance_states__value="Rejected").distinct()
        tag = self.request.GET.get('tag', "")
        if tag:
            q = q.filter(tags__value=tag)
        return q.order_by("name")


class ConceptDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer


class ConceptDocumentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, concept, format=None):
        files_result = solr_search_paginated(core="files", term=concept, page_number=request.GET.get('pageNumber', 1),
                                             rows_per_page=request.GET.get('pageSize', 100))
        files_result = list(files_result)
        documents = []
        for file in files_result[1]:
            doc_id = file['attr_document_id'][0]
            doc = Document.objects.get(id=doc_id)
            if doc:
                documents.append(doc)
        document_serializer = DocumentSerializer(
            instance=documents, many=True, context={'request': request})

        files_result.append(document_serializer.data)
        return Response(files_result)


class TagListAPIView(ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    

class WorkLogAPIView(ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()


class WorklogDetailAPIView(RetrieveUpdateDestroyAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationWorklogSerializer
    queryset = AnnotationWorklog.objects.all()


class AcceptanceStateValueAPIView(APIView):

    def get(self, request, format=None):
        return Response([state.value for state in AcceptanceStateValue])


class AcceptanceStateListAPIView(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AcceptanceStateSerializer

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
