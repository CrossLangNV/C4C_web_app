# Generated by Django 3.0.3 on 2020-02-18 13:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapyItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.CharField(max_length=100, null=True)),
                ('data', models.TextField()),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
