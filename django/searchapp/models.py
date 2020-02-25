import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from .solr_call import solr_add, solr_search_id


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
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    date = models.DateField(default=timezone.now)
    acceptance_state = models.CharField(max_length=20,
                                        choices=AcceptanceState.choices,
                                        default=AcceptanceState.UNVALIDATED)
    url = models.URLField(unique=True)
    website = models.ForeignKey('Website', on_delete=models.CASCADE)
    summary = models.TextField(default="")
    content = models.TextField(default="")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # fail-safe measure to prevent content to be cleared inadvertently
        if not self.content and not self.content.isspace():
            solr_data = solr_search_id('documents', str(self.id))
            if solr_data:
                self.content = solr_data[0]['content'][0]
        # add and index content to Solr
        solr_doc = {
            "id": str(self.id),
            "title": self.title,
            "date": self.date,
            "acceptance_state": self.acceptance_state,
            "url": self.url,
            "website": self.website,
            "summary": self.summary,
            "content": self.content
        }
        solr_add(core="documents", docs=[solr_doc])
        # clear document content so it doesn't get saved to django db
        self.content = ''
        super().save(*args, **kwargs)


class EiopaDocument(Document):
    title_prefix = models.CharField(max_length=500)
    type = models.CharField(max_length=200)
    pdf_urls = ArrayField(
        models.URLField(), default=list
    )
    pdf_file = models.FileField(upload_to='eiopa/' ,default=None)
