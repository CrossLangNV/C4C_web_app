# Generated by Django 3.0.9 on 2020-10-29 09:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('searchapp', '0037_document_unvalidated'),
        ('glossary', '0007_concept_lemma'),
    ]

    operations = [
    ]
