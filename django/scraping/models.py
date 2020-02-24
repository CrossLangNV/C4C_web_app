from django.db import models
from django.utils import timezone


class ScrapingTask(models.Model):
    spider = models.CharField(max_length=100, default="")
    date = models.DateTimeField(default=timezone.now)


class ScrapingTaskItem(models.Model):
    task = models.ForeignKey('ScrapingTask', on_delete=models.CASCADE)
    data = models.TextField()  # crawled data
    date = models.DateTimeField(default=timezone.now)
