# Generated by Django 4.2.9 on 2024-02-27 11:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_alter_account_username'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AccountUser',
        ),
        migrations.RemoveField(
            model_name='account',
            name='username',
        ),
    ]
