from django.db import models
import uuid
from .solr_call import solr_add

class Website(models.Model):
    name = models.CharField(max_length=32)
    content = models.TextField()
    url = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class AcceptanceState(models.TextChoices):
    UNVALIDATED = 'Unvalidated',
    ACCEPTED = 'Accepted',
    REJECTED = 'Rejected'

class Document(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    date = models.DateField()
    acceptance_state = models.CharField(max_length=20,
                                 choices=AcceptanceState.choices,
                                 default=AcceptanceState.UNVALIDATED)
    url = models.CharField(max_length=150)
    website = models.ForeignKey('Website', on_delete=models.CASCADE)
    content = models.TextField(default="")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # add and index content to Solr
        solr_doc = {
            "id": str(self.id),
            "title": self.title,
            "date": self.date,
            "acceptance_state": self.acceptance_state,
            "url": self.url,
            "website": self.website,
            "content": self.content
        }
        solr_add(core="documents", docs=[solr_doc])
        # clear document content so it doesn't get saved to django db
        self.content = ''
        super().save(*args, **kwargs)

