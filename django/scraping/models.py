from django.db import models
from django.utils import timezone


class ScrapingTask(models.Model):
    scheduler_id = models.CharField(max_length=100, default="")
    spider = models.CharField(max_length=100, default="")
    spider_type = models.CharField(max_length=100, default="")
    status = models.CharField(max_length=100, default="")
    date = models.DateTimeField(default=timezone.now)
