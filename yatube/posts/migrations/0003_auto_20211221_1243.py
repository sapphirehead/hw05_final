# Generated by Django 2.2.19 on 2021-12-21 09:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20211221_1240'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='address',
            new_name='slug',
        ),
    ]
