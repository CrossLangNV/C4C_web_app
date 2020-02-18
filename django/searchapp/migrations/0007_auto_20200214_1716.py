# Generated by Django 3.0.3 on 2020-02-14 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0006_auto_20200213_0830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='document',
            name='url',
            field=models.URLField(),
        ),
        migrations.AlterField(
            model_name='website',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='website',
            name='url',
            field=models.URLField(),
        ),
    ]