# Generated by Django 4.2.9 on 2024-02-09 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_product_brand'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='brand',
        ),
    ]
