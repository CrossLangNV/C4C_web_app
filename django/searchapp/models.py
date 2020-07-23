import binascii
import uuid

from django.db import models
from django.utils import timezone

from scheduler.pdf_handling import pdf_extract
from searchapp.solr_call import solr_delete, solr_update

import pysolr
import os


class Website(models.Model):
    name = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    url = models.URLField(unique=True)

    def __str__(self):
        return self.name


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    celex = models.CharField(max_length=20, default="", blank=True)

    title = models.CharField(max_length=1000)
    title_prefix = models.CharField(max_length=500, default="", blank=True)
    author = models.CharField(max_length=500, default="", blank=True)

    status = models.CharField(max_length=100, default="", blank=True)
    type = models.CharField(max_length=200, default="", blank=True)

    date = models.DateTimeField(default=timezone.now)
    date_last_update = models.DateTimeField(default=timezone.now)

    url = models.URLField(max_length=1000, unique=True)
    eli = models.URLField(default="", blank=True)

    website = models.ForeignKey(
        'Website', related_name='documents', on_delete=models.CASCADE)

    summary = models.TextField(default="", blank=True)
    various = models.TextField(default="", blank=True)
    consolidated_versions = models.TextField(default="", blank=True)

    file = models.FileField(null=True, blank=True)
    file_url = models.URLField(
        max_length=1000, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    acceptance_state_max_probability = models.FloatField(default=0.0)

    def __str__(self):
        return self.title

    def update_solr(self):
        # add and index data to Solr when it wasn't pulled from Solr first
        solr_doc = {}
        for field, value in self.__dict__.items():
            if field == 'website_id':
                solr_doc['website'] = self.website.name
            elif field == 'date' or field == 'created_at' or field == 'updated_at':
                solr_doc[field] = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            elif not field.startswith('_') and field != 'extract_text' and not field.startswith('content') and field != 'file' and field != 'pull':
                solr_doc[field] = value

        # Work around "Object of type UUID is not JSON serializable"
        solr_doc['id'] = str(solr_doc['id'])
        # Update solr
        solr_update("documents", solr_doc)

        # extract text from file if indicated
        if self.extract_text and self.file.name:
            pdf_extract.delay(
                binascii.b2a_base64(
                    self.file.read(), newline=False).decode('utf-8'),
                str(self.id)
            )

    def update_score(self, score, status):
        core = 'documents'
        client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
        document = {"id": str(self.id),
                    "accepted_probability": {"set": score},
                    "acceptance_state": {"set": status}}
        client.add(document)

    def delete(self, *args, **kwargs):
        # delete from Solr
        solr_delete(core='documents', id=str(self.id))
        super().delete(*args, **kwargs)


class AcceptanceStateValue(models.TextChoices):
    UNVALIDATED = 'Unvalidated',
    ACCEPTED = 'Accepted',
    REJECTED = 'Rejected'


class AcceptanceState(models.Model):
    value = models.CharField(max_length=20,
                             choices=AcceptanceStateValue.choices,
                             default=AcceptanceStateValue.UNVALIDATED, db_index=True)
    document = models.ForeignKey(
        'Document', related_name='acceptance_states', on_delete=models.CASCADE)
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, blank=True, null=True)
    probability_model = models.CharField(
        max_length=50, blank=True, null=True, db_index=True)
    accepted_probability = models.FloatField(default=0.0, blank=True)
    accepted_probability_index = models.IntegerField(default=0, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['document_id', 'user_id'], name="unique_per_doc_and_user"),
            models.UniqueConstraint(
                fields=['document_id', 'probability_model'], name="unique_per_doc_and_model")

        ]
        ordering = ['user']


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField()
    url = models.URLField(max_length=1000, unique=True)
    document = models.ForeignKey(
        'Document', related_name='attachments', on_delete=models.CASCADE)
    content = models.TextField(default="")
    extracted = models.BooleanField(default=False, editable=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


class Comment(models.Model):
    value = models.TextField()
    document = models.ForeignKey(
        'Document', related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    value = models.CharField(max_length=50)
    document = models.ForeignKey(
        'Document', related_name='tags', on_delete=models.CASCADE)

    def __str__(self):
        return self.value
