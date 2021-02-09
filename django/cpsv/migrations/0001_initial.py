# Generated by Django 3.0.9 on 2021-01-27 10:14

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('glossary', '0022_auto_20210126_1136'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=200)),
                ('opening_hours', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PublicService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('description', models.TextField()),
                ('identifier', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PublicServiceConcept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='glossary.Concept')),
                ('public_service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cpsv.PublicService')),
            ],
        ),
        migrations.AddField(
            model_name='publicservice',
            name='concepts',
            field=models.ManyToManyField(related_name='public_service_concept', through='cpsv.PublicServiceConcept', to='glossary.Concept'),
        ),
    ]
