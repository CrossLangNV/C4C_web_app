# Generated by Django 3.0.9 on 2020-10-21 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0038_auto_20201001_0800'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='language',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
