# Generated by Django 4.1.2 on 2022-11-03 11:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='filmwork',
            old_name='genres',
            new_name='genre',
        ),
    ]