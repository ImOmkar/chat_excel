# Generated by Django 5.0.1 on 2024-01-08 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadexcel',
            name='excel_file',
            field=models.FileField(upload_to='file_uploads\\'),
        ),
    ]
