# Generated by Django 3.0.9 on 2020-10-20 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0037_document_unvalidated'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='formex_available',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
