# Generated by Django 3.0.3 on 2020-02-24 09:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scrapingtask',
            name='unique_id',
        ),
    ]
