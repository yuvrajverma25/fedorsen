# Generated by Django 4.2.7 on 2023-11-21 16:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesscode',
            name='expiration_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 12, 21, 16, 45, 24, 554993, tzinfo=datetime.timezone.utc)),
        ),
    ]