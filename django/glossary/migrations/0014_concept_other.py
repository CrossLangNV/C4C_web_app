# Generated by Django 3.0.9 on 2020-12-24 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('glossary', '0013_concept_website'),
    ]

    operations = [
        migrations.AddField(
            model_name='concept',
            name='other',
            field=models.ManyToManyField(related_name='_concept_other_+', to='glossary.Concept'),
        ),
    ]