# Generated by Django 3.2.4 on 2021-07-02 12:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_auto_20210702_1256'),
    ]

    operations = [
        migrations.RenameField(
            model_name='genome',
            old_name='env_broad_scale_new',
            new_name='env_broad_scale',
        ),
        migrations.RenameField(
            model_name='genome',
            old_name='env_local_scale_new',
            new_name='env_local_scale',
        ),
        migrations.RenameField(
            model_name='genome',
            old_name='env_medium_new',
            new_name='env_medium',
        ),
    ]
