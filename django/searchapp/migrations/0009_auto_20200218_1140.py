# Generated by Django 3.0.3 on 2020-02-18 11:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0008_auto_20200218_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
