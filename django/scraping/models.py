from django.db import models
from django.utils import timezone


class ScrapingTask(models.Model):
    spider = models.CharField(max_length=100, default="")
    spider_type = models.CharField(max_length=100, default="")
    spider_date_start = models.DateField(null=True, blank=True)
    spider_date_end = models.DateField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)


class ScrapingTaskItem(models.Model):
    scheduler_id = models.CharField(max_length=100, default="")
    task = models.ForeignKey('ScrapingTask', related_name='items', on_delete=models.CASCADE)
    status = models.CharField(max_length=100, default="")
    date = models.DateTimeField(default=timezone.now)
