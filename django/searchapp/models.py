from django.db import models
import uuid

class Website(models.Model):
    name = models.CharField(max_length=32)
    content = models.TextField()
    url = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    date = models.DateField()
    url = models.CharField(max_length=150)
    website = models.ForeignKey('Website', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

