# Generated by Django 5.1.8 on 2025-04-26 06:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='milestones',
            old_name='target',
            new_name='target_metric',
        ),
        migrations.AddField(
            model_name='milestones',
            name='target_category',
            field=models.CharField(default='default', max_length=50),
            preserve_default=False,
        ),
    ]
