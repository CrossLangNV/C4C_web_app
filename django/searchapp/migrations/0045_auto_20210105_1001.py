# Generated by Django 3.0.9 on 2021-01-05 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0044_document_date_of_effect'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='date_of_effect',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
