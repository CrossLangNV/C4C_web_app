from django.urls import path

import os
from . import views

from django.urls import path, re_path, include

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Reporting Obligations API",
        default_version='v1',
        description="Documentation for REST API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="nobody@crosslang.com"),
        license=openapi.License(name="BSD License"),
    ),
    url=os.environ['DJANGO_BASE_URL'],
    patterns=[path('obligations/', include(('obligations.urls', 'obligations'), namespace="obligations"))],
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

    # Reporting Obligations
    path('api/ros', views.ReportingObligationListAPIView.as_view(), name='ro_api_list'),
    path('api/ro/<int:pk>', views.ReportingObligationDetailAPIView.as_view(), name='ro_api_detail'),

    #path('api/ro/<ro>', views.ReportingObligationDocumentsAPIView.as_view(), name='ro_api_search'),

    # RO splits
    path('api/ros/reporters', views.ReportingObligationReportersListAPIView.as_view(), name='ro_reporters_api_list'),
    path('api/ros/verbs', views.ReportingObligationVerbsListAPIView.as_view(), name='ro_verbs_api_list'),
    path('api/ros/reports', views.ReportingObligationReportsListAPIView.as_view(), name='ro_reports_api_list'),
    path('api/ros/regulatorybody', views.ReportingObligationRegulatoryBodyListAPIView.as_view(),
         name='ro_regulatorybody_api_list'),
    path('api/ros/propmod', views.ReportingObligationPropModListAPIView.as_view(), name='ro_propmod_api_list'),
    path('api/ros/entity', views.ReportingObligationEntityListAPIView.as_view(), name='ro_entity_api_list'),
    path('api/ros/frequency', views.ReportingObligationFrequencyListAPIView.as_view(), name='ro_frequency_api_list'),
    path('api/ros/rdfentities', views.ReportingObligationAvailableEntitiesAPIView.as_view(),
         name='ro_available_entities_api_list'),
    path('api/ros/predicate/<predicate>', views.ReportingObligationGetByPredicate.as_view(), name='ro_find_by_predicate'),

    # Replace the other one later
    path('api/rdf_ros', views.ReportingObligationsRDFListAPIView.as_view(), name='ro_rdf_api_list'),

    # Query RDF
    path('api/ros/query/single', views.ReportingObligationQuerySingleAPIView.as_view(), name='ro_rdf_api_query_single'),
    path('api/ros/query', views.ReportingObligationQueryMultipleAPIView.as_view(), name='ro_rdf_api_query_multiple'),
]