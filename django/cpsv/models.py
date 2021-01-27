
from django.db import models
from django.utils import timezone

from glossary.models import Concept


class PublicService(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField()
    identifier = models.CharField(max_length=200)

    concepts = models.ManyToManyField(
        Concept,
        through='PublicServiceConcept',
        through_fields=('public_service', 'concept'),
        related_name='public_service_concept'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PublicServiceConcept(models.Model):
    public_service = models.ForeignKey(PublicService, on_delete=models.CASCADE)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)


class ContactPoint(models.Model):
    identifier = models.CharField(max_length=200)
    opening_hours = models.TextField()

