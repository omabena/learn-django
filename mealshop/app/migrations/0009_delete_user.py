# Generated by Django 3.0.6 on 2020-06-10 13:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_user'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]