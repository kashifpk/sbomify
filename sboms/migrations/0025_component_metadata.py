# Generated by Django 5.1 on 2024-10-03 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sboms", "0024_remove_sbom_data_sbom_sbom_filename"),
    ]

    operations = [
        migrations.AddField(
            model_name="component",
            name="metadata",
            field=models.JSONField(default=dict),
        ),
    ]
