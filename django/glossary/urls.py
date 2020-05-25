import os

from django.urls import path, re_path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from glossary import views

schema_view = get_schema_view(
    openapi.Info(
        title="Glossary of Concepts API",
        default_version='v1',
        description="Documentation for REST API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="nobody@crosslang.com"),
        license=openapi.License(name="BSD License"),
    ),
    url=os.environ['DJANGO_BASE_URL'],
    patterns=[path('glossary/', include(('glossary.urls', 'glossary'), namespace="glossary"))],
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [

    # API
    # Swagger drf-yasg
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger', schema_view.with_ui(
        'swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc', schema_view.with_ui(
        'redoc', cache_timeout=0), name='schema-redoc'),

    # Concept
    path('api/concepts', views.ConceptListAPIView.as_view(), name='concept_api_list'),
    path('api/concept/<int:pk>', views.ConceptDetailAPIView.as_view(), name='concept_api_detail'),
    path('api/concept/<concept>', views.ConceptDocumentsAPIView.as_view(), name='concept_api_search'),
]
