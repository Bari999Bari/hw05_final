# Generated by Django 2.2.6 on 2022-03-19 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220308_1758'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ('pk',)},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',), 'verbose_name': 'Post'},
        ),
    ]
