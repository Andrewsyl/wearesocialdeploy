# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_auto_20151210_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='subsciption_end',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 10, 10, 18, 49, 563000, tzinfo=utc)),
        ),
    ]
