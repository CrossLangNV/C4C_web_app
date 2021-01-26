from time import timezone

from django.db import models

from glossary.models import Concept


class CpsvBase(models.Model):
    title = models.TextField(unique=True)
    url = models.CharField(max_length=200)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['title']

    def __str__(self):
        return self.title


class PublicService(CpsvBase):
    class Meta(CpsvBase.Meta):
        pass


class ContactPoint(CpsvBase):
    class Meta(CpsvBase.Meta):
        pass


class LiveEvent(CpsvBase):
    class Meta(CpsvBase.Meta):
        pass


class Phone(models.Model):
    value = models.CharField(max_length=200, db_index=True)
