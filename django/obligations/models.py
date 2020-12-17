from django.db import models
from django.utils import timezone


# Create your models here.

class ReportingObligation(models.Model):
    rdf_id = models.CharField(max_length=200, null=True)
    name = models.TextField()
    definition = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AcceptanceStateValue(models.TextChoices):
    UNVALIDATED = 'Unvalidated',
    ACCEPTED = 'Accepted',
    REJECTED = 'Rejected'


class AcceptanceState(models.Model):
    value = models.CharField(max_length=20,
                             choices=AcceptanceStateValue.choices,
                             default=AcceptanceStateValue.UNVALIDATED, db_index=True)
    reporting_obligation = models.ForeignKey(
        'ReportingObligation', related_name='acceptance_states', on_delete=models.CASCADE)
    user = models.ForeignKey(
        'auth.User', related_name="obligation_acceptance_state", on_delete=models.CASCADE, blank=True, null=True)
    probability_model = models.CharField(
        max_length=50, blank=True, null=True, db_index=True)
    accepted_probability = models.FloatField(default=0.0, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reporting_obligation_id', 'user_id'], name="unique_per_reporting_obligation_and_user"),
            models.UniqueConstraint(
                fields=['reporting_obligation_id', 'probability_model'],
                name="unique_per_reporting_obligation_and_model")

        ]
        ordering = ['user']


class Comment(models.Model):
    value = models.TextField()
    reporting_obligation = models.ForeignKey(
        'ReportingObligation', related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(
        'auth.User', related_name="obligation_comment",  on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    value = models.CharField(max_length=50)
    reporting_obligation = models.ForeignKey(
        'ReportingObligation', related_name='tags', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.value