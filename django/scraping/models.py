from django.db import models
from django.utils import timezone


class ScrapyItem(models.Model):
    unique_id = models.CharField(max_length=100, null=True)
    spider = models.CharField(max_length=100, default="")
    data = models.TextField()  # crawled data
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.unique_id

    def save(self, *args, **kwargs):
        # TODO: postprocess

        super().save(*args, **kwargs)
