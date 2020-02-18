from django.contrib.auth.decorators import login_required
from django.urls import path
from scraping import views

urlpatterns = [
    path('', views.ScrapingTemplateView.as_view(), name='scraping'),
]