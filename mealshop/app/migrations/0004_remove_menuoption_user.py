# Generated by Django 3.0.6 on 2020-06-10 04:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20200610_0028'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menuoption',
            name='user',
        ),
    ]
