import uuid

from django.db import models
from django.utils import timezone

from searchapp.solr_call import solr_add, solr_delete, solr_add_file


class Website(models.Model):
    name = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    url = models.URLField(unique=True)

    def __str__(self):
        return self.name


class AcceptanceState(models.TextChoices):
    UNVALIDATED = 'Unvalidated',
    ACCEPTED = 'Accepted',
    REJECTED = 'Rejected'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    title_prefix = models.CharField(max_length=500, default="")
    type = models.CharField(max_length=200, default="")
    date = models.DateField(default=timezone.now)
    acceptance_state = models.CharField(max_length=20,
                                        choices=AcceptanceState.choices,
                                        default=AcceptanceState.UNVALIDATED)
    url = models.URLField(unique=True)
    website = models.ForeignKey('Website', related_name='documents', on_delete=models.CASCADE)
    summary = models.TextField(default="")
    content = models.TextField(default="")
    pull = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # add and index data to Solr when it wasn't pulled from Solr first
        if not self.pull:
            solr_doc = {}
            for field, value in self.__dict__.items():
                if field == 'website_id':
                    solr_doc['website'] = self.website.name
                elif field != '_state':
                    solr_doc[field] = value
            solr_add(core="documents", docs=[solr_doc])
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # delete from Solr
        solr_delete(core='documents', id=str(self.id))
        super().delete(*args, **kwargs)


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField()
    url = models.URLField(unique=True)
    document = models.ForeignKey('Document', related_name='attachments', on_delete=models.CASCADE)
    pull = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        # add and index data to Solr when it wasn't pulled from Solr first
        if not self.pull and self.file.name:
            solr_add_file('files', self.file, self.id, self.url, str(self.document.id))

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # delete from Solr
        solr_delete(core='files', id=str(self.id))
        super().delete(*args, **kwargs)
