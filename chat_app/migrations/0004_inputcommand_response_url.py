# Generated by Django 5.0.1 on 2024-01-09 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_app', '0003_alter_uploadexcel_excel_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='inputcommand',
            name='response_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]