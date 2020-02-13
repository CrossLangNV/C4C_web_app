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
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path
from searchapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.search_index, name='search_view'),

    path('website/', login_required(views.WebsiteListView.as_view(), login_url='login'), name='websites'),
    path('website/create/', login_required(views.WebsiteCreateView.as_view(), login_url='login'),
         name='create_website'),
    path('website/<int:pk>/', login_required(views.WebsiteDetailView.as_view(), login_url='login'), name='website'),
    path('website/<int:pk>/create/', login_required(views.DocumentCreateView.as_view(), login_url='login'),
         name='create_document'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('api/films/', views.FilmList.as_view(), name='film-list'),
    path('api/films/<search_term>/', views.Film.as_view(), name='film-search')
]
