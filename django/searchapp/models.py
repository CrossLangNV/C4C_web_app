from django.db import models
import uuid

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

    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
        # saver = SolrSaver()
        # saver.save()
        # self.save()

