from django.db import models
from django.utils import timezone


# Create your models here.

class ReportingObligation(models.Model):
    name = models.CharField(max_length=200)
    definition = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
