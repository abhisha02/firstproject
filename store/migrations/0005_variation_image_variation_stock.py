# Generated by Django 4.2.9 on 2024-01-22 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_rename_addimage_productimage_addimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='variation',
            name='image',
            field=models.ImageField(default='default.jpg', upload_to='photos/products'),
        ),
        migrations.AddField(
            model_name='variation',
            name='stock',
            field=models.IntegerField(default=0),
        ),
    ]