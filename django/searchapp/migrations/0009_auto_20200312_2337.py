# Generated by Django 3.0.3 on 2020-03-12 23:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('searchapp', '0008_auto_20200312_0851'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='acceptance_state',
        ),
        migrations.CreateModel(
            name='AcceptanceState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(choices=[('Unvalidated', 'Unvalidated'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], default='Unvalidated', max_length=20)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acceptance_states', to='searchapp.Document')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
