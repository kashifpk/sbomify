# Generated by Django 5.0.4 on 2024-06-08 03:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sboms", "0003_rename_cpe_id_package_purl_package_data"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="sbom",
            unique_together={("project", "name", "created_at")},
        ),
    ]
