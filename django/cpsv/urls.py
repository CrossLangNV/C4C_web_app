from django.urls import path

import os

from django.urls import path, re_path, include

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions

from cpsv import views


schema_view = get_schema_view(
    openapi.Info(
        title="CPSV API",
        default_version='v1',
        description="Documentation for REST API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="nobody@crosslang.com"),
        license=openapi.License(name="BSD License"),
    ),
    url=os.environ['DJANGO_BASE_URL'],
    patterns=[path('cpsv/', include(('cpsv.urls', 'cpsv'), namespace="cpsv"))],
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

    path('api/rdf_contact_points', views.RdfContactPointsAPIView.as_view(),
         name='rdf_contact_points_api_list'),

    path('api/rdf_public_services', views.RdfPublicServicesAPIView.as_view(),
         name='rdf_contact_points_api_list'),

    path('api/ps/<int:pk>', views.PublicServiceDetailAPIView.as_view(), name='ps_api_detail'),
    path('api/cp/<int:pk>', views.ContactPointDetailAPIView.as_view(), name='cp_api_detail'),

    path('api/ps/entity_map', views.PublicServicesEntityOptionsAPIView.as_view(), name='ps_entity_options'),

    path('api/dropdown_options', views.DropdownOptionsAPIView.as_view(), name='dropdown_public_services'),

]