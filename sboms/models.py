from django.apps import apps
from django.db import models

from core.utils import generate_id
from teams.models import Team


class Product(models.Model):
    class Meta:
        db_table = apps.get_app_config("sboms").name + "_products"
        unique_together = ("team", "name")
        ordering = ["name"]

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    projects = models.ManyToManyField("sboms.Project", through="sboms.ProductProject")

    def __str__(self) -> str:
        return f"{self.name}(Team ID: {self.team_id})"


class Project(models.Model):
    class Meta:
        db_table = apps.get_app_config("sboms").name + "_projects"
        unique_together = ("team", "name")
        ordering = ["name"]

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    products = models.ManyToManyField(Product, through="sboms.ProductProject")
    components = models.ManyToManyField("sboms.Component", through="sboms.ProjectComponent")

    def __str__(self) -> str:
        return f"<{self.id}> {self.name}"


class ProductProject(models.Model):
    class Meta:
        db_table = apps.get_app_config("sboms").name + "_products_projects"
        unique_together = ("product", "project")

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.product_id} - {self.project_id}"


class Component(models.Model):
    class Meta:
        db_table = apps.get_app_config("sboms").name + "_components"
        unique_together = ("team", "name")
        ordering = ["name"]

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    projects = models.ManyToManyField(Project, through="sboms.ProjectComponent")

    def __str__(self) -> str:
        return f"{self.name}"

    @property
    def latest_sbom(self) -> "SBOM":
        return self.sbom_set.order_by("-created_at").first()


class ProjectComponent(models.Model):
    class Meta:
        db_table = apps.get_app_config("sboms").name + "_projects_components"
        unique_together = ("project", "component")

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.project_id} - {self.component_id}"


class SBOM(models.Model):
    class Meta:
        db_table = apps.get_app_config("sboms").name + "_sboms"
        ordering = ["-created_at"]

    id = models.CharField(max_length=20, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255, blank=False)  # qualified sbom name like com.github.sbomify/backend
    version = models.CharField(max_length=255, default="")
    format = models.CharField(max_length=255, default="spdx")  # spdx, cyclonedx, etc
    format_version = models.CharField(max_length=20, default="")
    licenses = models.JSONField(default=list)
    packages_licenses = models.JSONField(default=dict)
    sbom_filename = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    # Where the sbom came from (file-upload, api, github-action, etc)
    source = models.CharField(max_length=255, null=True)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name

    @property
    def public_access_allowed(self) -> bool:
        return self.component.is_public
