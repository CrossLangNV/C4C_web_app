# Generated by Django 3.0.3 on 2020-02-24 11:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0002_remove_scrapingtask_unique_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapingtaskitem',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='scraping.ScrapingTask'),
        ),
    ]
