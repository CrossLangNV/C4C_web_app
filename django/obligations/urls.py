from django.urls import path

from . import views

urlpatterns = [
    # Reporting Obligations
    path('api/ros', views.ReportingObligationListAPIView.as_view(), name='ro_api_list'),
    path('api/ro/<int:pk>', views.ReportingObligationDetailAPIView.as_view(), name='ro_api_detail'),
    path('api/ro/<ro>', views.ReportingObligationDocumentsAPIView.as_view(), name='ro_api_search'),
]