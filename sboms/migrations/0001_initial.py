# Generated by Django 5.0.4 on 2024-06-04 02:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("teams", "0003_invitation_expires_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="Package",
            fields=[
                ("cpe_id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("license_name", models.CharField(null=True)),
            ],
            options={
                "db_table": "sboms_packages",
            },
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "team",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="teams.team"),
                ),
            ],
            options={
                "db_table": "sboms_projects",
                "unique_together": {("team", "name")},
            },
        ),
        migrations.CreateModel(
            name="SBOM",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("data", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sboms.project"
                    ),
                ),
            ],
            options={
                "db_table": "sboms_sboms",
            },
        ),
        migrations.CreateModel(
            name="SBOMPackage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "package",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sboms.package"
                    ),
                ),
                (
                    "sbom",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="sboms.sbom"),
                ),
            ],
            options={
                "db_table": "sboms_sbom_packages",
                "unique_together": {("sbom", "package")},
            },
        ),
        migrations.AddField(
            model_name="sbom",
            name="packages",
            field=models.ManyToManyField(through="sboms.SBOMPackage", to="sboms.package"),
        ),
        migrations.AlterUniqueTogether(
            name="sbom",
            unique_together={("project", "name")},
        ),
    ]
