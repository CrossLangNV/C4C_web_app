# Generated by Django 3.0.5 on 2020-05-07 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('searchapp', '0022_auto_20200506_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acceptancestate',
            name='probability_model',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='acceptancestate',
            name='value',
            field=models.CharField(choices=[('Unvalidated', 'Unvalidated'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], db_index=True, default='Unvalidated', max_length=20),
        ),
    ]
