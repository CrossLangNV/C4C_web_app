from django.urls import path

from scraping import views

urlpatterns = [
    path('', views.ScrapingTemplateView.as_view(), name='scraping'),
    path('<spider>', views.ScrapingTemplateView.as_view(), name='spider'),
]
