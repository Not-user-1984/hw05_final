# Generated by Django 2.2.16 on 2022-08-26 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_auto_20220823_1316'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user_id', 'author_id'), name='unique_follows'),
        ),
    ]
