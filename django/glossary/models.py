from django.db import models

from searchapp.models import Document


class Concept(models.Model):
    name = models.CharField(max_length=200, unique=True)
    definition = models.TextField()
    documents = models.ManyToManyField(Document)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
