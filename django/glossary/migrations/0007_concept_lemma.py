# Generated by Django 3.0.9 on 2020-10-14 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('glossary', '0006_auto_20201012_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='concept',
            name='lemma',
            field=models.CharField(default='', max_length=200),
        ),
    ]
