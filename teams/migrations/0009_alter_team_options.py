# Generated by Django 5.1 on 2024-11-04 15:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0008_team_branding_info"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="team",
            options={"ordering": ["name"]},
        ),
    ]
