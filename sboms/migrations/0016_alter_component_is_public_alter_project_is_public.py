# Generated by Django 5.0.4 on 2024-07-27 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sboms", "0015_alter_component_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="component",
            name="is_public",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="project",
            name="is_public",
            field=models.BooleanField(default=False),
        ),
    ]
