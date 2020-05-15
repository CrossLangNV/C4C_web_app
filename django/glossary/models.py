from django.db import models


class Concept(models.Model):
    name = models.CharField(max_length=200, unique=True)
    definition = models.TextField()

    def __str__(self):
        return self.name
