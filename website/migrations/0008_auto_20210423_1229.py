# Generated by Django 3.2 on 2021-04-23 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0007_auto_20210413_0536'),
    ]

    operations = [
        migrations.AddField(
            model_name='genome',
            name='assembly_gaps',
            field=models.IntegerField(blank=True, null=True, verbose_name='Number of gaps'),
        ),
        migrations.AddField(
            model_name='genome',
            name='assembly_ncount',
            field=models.IntegerField(blank=True, null=True, verbose_name='Total Ns'),
        ),
    ]
