# Generated by Django 4.2.9 on 2024-01-22 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_alter_profile_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='uid',
            field=models.CharField(default='<function uuid4 at 0x0000015B47DFBEC0>', max_length=200),
        ),
    ]
