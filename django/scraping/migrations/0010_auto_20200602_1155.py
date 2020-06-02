# Generated by Django 3.0.5 on 2020-06-02 11:55

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0009_auto_20200602_1137'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scrapingtask',
            name='status',
        ),
        migrations.AddField(
            model_name='scrapingtaskitem',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='scrapingtaskitem',
            name='status',
            field=models.CharField(default='', max_length=100),
        ),
    ]