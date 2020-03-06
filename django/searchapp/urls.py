"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path

from searchapp import views

urlpatterns = [
    path('', login_required(views.WebsiteListView.as_view(), login_url='searchapp:login'), name='websites'),
    path('website/', login_required(views.WebsiteListView.as_view(), login_url='searchapp:login'), name='websites'),
    path('website/create/', login_required(views.WebsiteCreateView.as_view(), login_url='searchapp:login'),
         name='create_website'),
    path('website/<int:pk>/update/', login_required(views.WebsiteUpdateView.as_view(), login_url='searchapp:login'),
         name='update_website'),
    path('website/<int:pk>/delete/', login_required(views.WebsiteDeleteView.as_view(), login_url='searchapp:login'),
         name='delete_website'),
    path('website/<int:pk>/', login_required(views.WebsiteDetailView.as_view(), login_url='searchapp:login'),
         name='website'),
    path('website/<int:pk>/create/', login_required(views.DocumentCreateView.as_view(), login_url='searchapp:login'),
         name='create_document'),

    path('document/', login_required(views.DocumentSearchView.as_view(), login_url='searchapp:login'),
         name='document_search'),
    path('document/<uuid:pk>/', login_required(views.DocumentDetailView.as_view(), login_url='searchapp:login'),
         name='document'),
    path('document/<uuid:pk>/update/', login_required(views.DocumentUpdateView.as_view(), login_url='searchapp:login'),
         name='update_document'),
    path('document/<uuid:pk>/delete/', login_required(views.DocumentDeleteView.as_view(), login_url='searchapp:login'),
         name='delete_document'),

    path('login/', auth_views.LoginView.as_view(template_name='searchapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('films/', login_required(views.FilmSearchView.as_view(), login_url='searchapp:login'), name='films'),
    path('api/films/', views.FilmList.as_view(), name='film-list'),
    path('api/films/<search_term>/', views.Film.as_view(), name='film-search'),

    path('api/website/', views.WebsiteListAPIView.as_view(), name='website_list_api'),
    path('api/website/<int:pk>/', views.WebsiteDetailAPIView.as_view(), name='website_detail_api'),
    path('api/document/', views.DocumentListAPIView.as_view(), name='document_list_api'),
    path('api/document/<uuid:pk>/', views.DocumentDetailAPIView.as_view(), name='document_detail_api'),
    path('api/attachment/', views.AttachmentListAPIView.as_view(), name='attachment_list_api'),
    path('api/attachment/<uuid:pk>/', views.AttachmentDetailAPIView.as_view(), name='attachment_detail_api'),
    path('api/solrfiles/', views.SolrFileList.as_view(), name='solr_file_list_api'),
    path('api/solrfiles/<search_term>', views.SolrFile.as_view(), name='solr_file_search_api'),
    path('api/solrdocument/<id>', views.SolrDocument.as_view(), name='solr_document_api'),
]
