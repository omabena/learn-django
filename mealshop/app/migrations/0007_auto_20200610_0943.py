# Generated by Django 3.0.6 on 2020-06-10 13:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20200610_0937'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Employee',
        ),
        migrations.DeleteModel(
            name='Provider',
        ),
    ]