# Generated by Django 3.0.8 on 2020-07-28 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0031_auto_20200723_0836'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='acceptance_state_max_probability',
            field=models.FloatField(null=True),
        ),
        migrations.RunSQL(
            "UPDATE searchapp_document SET acceptance_state_max_probability= NULL")
    ]