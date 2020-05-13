from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from searchapp.models import Document
from searchapp.serializers import DocumentSerializer
from searchapp.solr_call import solr_search_paginated


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
        document_serializer = DocumentSerializer(instance=documents, many=True, context={'request': request})

        files_result.append(document_serializer.data)
        return Response(files_result)
