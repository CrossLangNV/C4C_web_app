# Generated by Django 3.0.5 on 2020-04-16 11:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0017_auto_20200416_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='attachment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
