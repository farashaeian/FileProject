# Generated by Django 4.0.6 on 2022-09-14 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('count', '0005_rename_task_id_file_task_result'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='task_result',
        ),
        migrations.AddField(
            model_name='file',
            name='task_id',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
