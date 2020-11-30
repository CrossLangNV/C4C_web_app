# Generated by Django 3.0.9 on 2020-10-27 10:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0037_document_unvalidated'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('glossary', '0007_concept_lemma'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='concept',
            name='documents',
        ),
        migrations.CreateModel(
            name='ConceptOccurs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probability', models.FloatField(blank=True, default=0.0)),
                ('begin', models.IntegerField()),
                ('end', models.IntegerField()),
                ('concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='glossary.Concept')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='searchapp.Document')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConceptDefined',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probability', models.FloatField(blank=True, default=0.0)),
                ('begin', models.IntegerField()),
                ('end', models.IntegerField()),
                ('concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='glossary.Concept')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='searchapp.Document')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnnotationWorklog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('add', 'Add concept'), ('del', 'Delete concept')], max_length=3)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('concept_defined', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='glossary.ConceptDefined')),
                ('concept_occurs', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='glossary.ConceptOccurs')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='searchapp.Document')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_worklog', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='concept',
            name='document_defined',
            field=models.ManyToManyField(related_name='definition', through='glossary.ConceptDefined', to='searchapp.Document'),
        ),
        migrations.AddField(
            model_name='concept',
            name='document_occurs',
            field=models.ManyToManyField(related_name='occurrance', through='glossary.ConceptOccurs', to='searchapp.Document'),
        ),
        migrations.AddConstraint(
            model_name='conceptoccurs',
            constraint=models.UniqueConstraint(fields=('concept_id', 'document_id'), name='unique_per_conceptoccurs_and_document'),
        ),
        migrations.AddConstraint(
            model_name='conceptdefined',
            constraint=models.UniqueConstraint(fields=('concept_id', 'document_id'), name='unique_per_conceptdefined_and_document'),
        ),
    ]
