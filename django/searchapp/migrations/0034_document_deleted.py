# Generated by Django 3.0.9 on 2020-08-04 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0033_auto_20200729_1356'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='deleted',
            field=models.DateTimeField(editable=False, null=True),
        ),
    ]