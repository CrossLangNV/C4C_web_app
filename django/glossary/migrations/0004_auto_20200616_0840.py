# Generated by Django 3.0.5 on 2020-06-16 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0028_document_content_html'),
        ('glossary', '0003_auto_20200615_1209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concept',
            name='documents',
            field=models.ManyToManyField(blank=True, to='searchapp.Document'),
        ),
    ]
