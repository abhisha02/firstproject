# Generated by Django 4.2.9 on 2024-02-09 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0004_rename_cat_is_available_category_is_available'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand_name', models.CharField(max_length=50)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, max_length=255)),
                ('brand_image', models.ImageField(blank=True, upload_to='photos/brand/')),
                ('is_available', models.BooleanField(default=True)),
            ],
        ),
    ]