from django.urls import path

from scraping import views

urlpatterns = [
    path('', views.ScrapingTemplateView.as_view(), name='scraping'),
    path('<spider>/', views.ScrapingTemplateView.as_view(), name='spider'),

    path('api/task/', views.ScrapingItemList.as_view(), name='scraping-task'),
    path('api/task/<int:pk>/postprocess/', views.PostprocessScrapyItem.as_view(), name='postprocess'),
]
