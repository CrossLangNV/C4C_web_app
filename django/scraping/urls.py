from django.urls import path

from scraping import views

urlpatterns = [
    path('api/task/', views.ScrapingTaskListView.as_view(), name='scraping-task-list'),
]
