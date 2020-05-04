# Generated by Django 3.0.5 on 2020-05-04 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0020_auto_20200501_1107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='url',
            field=models.URLField(max_length=1000, unique=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='url',
            field=models.URLField(max_length=1000, unique=True),
        ),
    ]
