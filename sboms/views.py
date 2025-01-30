from __future__ import annotations

import tempfile
import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from django.http import HttpRequest

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.shortcuts import redirect, render

from core.errors import error_response
from core.object_store import S3Client
from core.utils import get_current_team_id, token_to_number
from teams.schemas import BrandingInfo

# from .decorators import validate_role_in_current_team
from .forms import NewComponentForm, NewProductForm, NewProjectForm
from .models import SBOM, Component, Product, Project
from .utils import get_project_sbom_package, verify_item_access


@login_required
def products_dashboard(request: HttpRequest) -> HttpResponse:
    team_id = get_current_team_id(request)
    if team_id is None:
        return error_response(request, HttpResponseBadRequest("No current team selected"))

    if request.method == "POST":
        form = NewProductForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    product = Product(
                        name=form.cleaned_data["name"],
                        team_id=team_id,
                    )
                    product.save()

                messages.add_message(
                    request,
                    messages.INFO,
                    f"Product {product.name} created",
                )

                return redirect("sboms:products_dashboard")
            except IntegrityError:
                form.add_error("name", "A product with this name already exists in this team")
                return render(
                    request,
                    "sboms/products_dashboard.html",
                    {
                        "products": Product.objects.filter(team_id=team_id).all(),
                        "new_product_form": form,
                        "has_crud_permissions": request.session.get("current_team").get("role") in ("owner", "admin"),
                    },
                )

    products = Product.objects.filter(team_id=team_id).all()
    new_product_form = NewProductForm()

    has_crud_permissions = request.session.get("current_team").get("role") in ("owner", "admin")

    return render(
        request,
        "sboms/products_dashboard.html",
        {
            "products": products,
            "new_product_form": new_product_form,
            "has_crud_permissions": has_crud_permissions,
        },
    )


def product_details_public(request: HttpRequest, product_id: str) -> HttpResponse:
    try:
        product: Product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Product not found"))

    # Verify access to project
    if not product.is_public:
        return error_response(request, HttpResponseNotFound("Product not found"))

    branding_info = BrandingInfo(**product.team.branding_info)
    return render(
        request,
        "sboms/product_details_public.html",
        {"product": product, "brand": branding_info},
    )


@login_required
def product_details_private(request: HttpRequest, product_id: str) -> HttpResponse:
    try:
        product: Product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Product not found"))

    # Verify access to project
    if not verify_item_access(request, product, ["guest", "owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for members of the team"))

    if request.method == "POST":
        selected_project_ids = [v for k, v in request.POST.items() if k.startswith("project_")]
        selected_projects = Project.objects.filter(id__in=selected_project_ids).all()

        for selected_project in selected_projects:
            if not verify_item_access(request, selected_project, ["owner", "admin"]):
                return error_response(request, HttpResponseForbidden("You're not allowed to perform this operation"))

        if request.GET.get("action", "") == "add_projects":
            with transaction.atomic():
                for selected_project in selected_projects:
                    product.projects.add(selected_project)

                product.save()

        elif request.GET.get("action", "") == "remove_projects":
            with transaction.atomic():
                for selected_project in selected_projects:
                    product.projects.remove(selected_project)

                product.save()

    product_projects_ids = product.projects.values_list("id", flat=True)

    team_id = get_current_team_id(request)
    if team_id is None:
        return error_response(request, HttpResponseBadRequest("No current team selected"))

    remaining_projects = Project.objects.filter(team_id=team_id).exclude(id__in=product_projects_ids).all()

    has_crud_permissions = verify_item_access(request, product, ["owner", "admin"])

    return render(
        request,
        "sboms/product_details_private.html",
        {
            "product": product,
            "has_crud_permissions": has_crud_permissions,
            "APP_BASE_URL": settings.APP_BASE_URL,
            "remaining_projects": remaining_projects,
            "current_team": request.session.get("current_team", {}),
        },
    )


@login_required
def delete_product(request: HttpRequest, product_id: str) -> HttpResponse:
    try:
        product: Product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Product not found"))

    if not verify_item_access(request, product, ["owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for owners or admins of the product"))

    product.delete()

    messages.add_message(
        request,
        messages.INFO,
        f"Product {product.name} deleted",
    )

    return redirect("sboms:products_dashboard")


@login_required
def projects_dashboard(request: HttpRequest) -> HttpResponse:
    team_id = get_current_team_id(request)
    if team_id is None:
        return error_response(request, HttpResponseBadRequest("No current team selected"))

    if request.method == "POST":
        form = NewProjectForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    project = Project(
                        team_id=team_id,
                        name=form.cleaned_data["name"],
                    )
                    project.save()

                messages.add_message(
                    request,
                    messages.INFO,
                    f"Project {project.name} created",
                )

                return redirect("sboms:projects_dashboard")
            except IntegrityError:
                form.add_error("name", "A project with this name already exists in this team")
                return render(
                    request,
                    "sboms/projects_dashboard.html",
                    {
                        "projects": Project.objects.filter(team_id=team_id).all(),
                        "new_project_form": form,
                        "has_crud_permissions": request.session.get("current_team").get("role") in ("owner", "admin"),
                    },
                )

    projects = Project.objects.filter(team_id=team_id).all()
    new_project_form = NewProjectForm()

    has_crud_permissions = request.session.get("current_team").get("role") in ("owner", "admin")

    return render(
        request,
        "sboms/projects_dashboard.html",
        {
            "projects": projects,
            "new_project_form": new_project_form,
            "has_crud_permissions": has_crud_permissions,
        },
    )


def project_details_public(request: HttpRequest, project_id: str) -> HttpResponse:
    try:
        project: Project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Project not found"))

    # Verify access to project
    if not project.is_public:
        return error_response(request, HttpResponseNotFound("Project not found"))

    branding_info = BrandingInfo(**project.team.branding_info)

    return render(
        request,
        "sboms/project_details_public.html",
        {"project": project, "brand": branding_info},
    )


@login_required
def project_details_private(request: HttpRequest, project_id: str) -> HttpResponse:
    try:
        project: Project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Project not found"))

    # Verify access to project
    if not verify_item_access(request, project, ["guest", "owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for members of the team"))

    if request.method == "POST":
        selected_component_ids = [v for k, v in request.POST.items() if k.startswith("component_")]
        selected_components = Component.objects.filter(id__in=selected_component_ids).all()

        for selected_component in selected_components:
            if not verify_item_access(request, selected_component, ["owner", "admin"]):
                return error_response(request, HttpResponseForbidden("You're not allowed to perform this operation"))

        if request.GET.get("action", "") == "add_components":
            with transaction.atomic():
                for selected_component in selected_components:
                    project.components.add(selected_component)

                project.save()

        elif request.GET.get("action", "") == "remove_components":
            with transaction.atomic():
                for selected_component in selected_components:
                    project.components.remove(selected_component)

                project.save()

    project_components_ids = project.components.values_list("id", flat=True)
    team_id = get_current_team_id(request)
    if team_id is None:
        return error_response(request, HttpResponseBadRequest("No current team selected"))

    remaining_components = Component.objects.filter(team_id=team_id).exclude(id__in=project_components_ids).all()

    has_crud_permissions = verify_item_access(request, project, ["owner", "admin"])
    has_private_components = False
    for component in project.components.all():
        if not component.is_public:
            has_private_components = True
            break

    return render(
        request,
        "sboms/project_details_private.html",
        {
            "project": project,
            "has_crud_permissions": has_crud_permissions,
            "APP_BASE_URL": settings.APP_BASE_URL,
            "remaining_components": remaining_components,
            "has_private_components": has_private_components,
            "current_team": request.session.get("current_team", {}),
        },
    )


@login_required
def delete_project(request: HttpRequest, project_id: str) -> HttpResponse:
    try:
        project: Project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Project not found"))

    if not verify_item_access(request, project, ["owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for owners or admins of the project"))

    project.delete()

    messages.add_message(
        request,
        messages.INFO,
        f"Project {project.name} deleted",
    )

    return redirect("sboms:projects_dashboard")


@login_required
def components_dashboard(request: HttpRequest) -> HttpResponse:
    team_id = get_current_team_id(request)
    if team_id is None:
        return error_response(request, HttpResponseBadRequest("No current team selected"))

    if request.method == "POST":
        form = NewComponentForm(request.POST)
        if not form.is_valid():
            messages.add_message(
                request,
                messages.ERROR,
                "Invalid form data",
            )
            return redirect("sboms:components_dashboard")
        else:
            try:
                with transaction.atomic():
                    component = Component(
                        team_id=team_id,
                        name=form.cleaned_data["name"],
                    )
                    component.save()

                messages.add_message(
                    request,
                    messages.INFO,
                    f"Component {component.name} created",
                )
                return redirect("sboms:components_dashboard")
            except IntegrityError:
                form.add_error("name", "A component with this name already exists in this team")
                return render(
                    request,
                    "sboms/components_dashboard.html",
                    {
                        "components": Component.objects.filter(team_id=team_id).all(),
                        "new_component_form": form,
                        "has_crud_permissions": request.session.get("current_team").get("role") in ("owner", "admin"),
                        "APP_BASE_URL": settings.APP_BASE_URL,
                    },
                )

    new_component_form = NewComponentForm()
    components = Component.objects.filter(team_id=team_id).all()
    has_crud_permissions = request.session.get("current_team").get("role") in ("owner", "admin")

    return render(
        request,
        "sboms/components_dashboard.html",
        {
            "components": components,
            "new_component_form": new_component_form,
            "has_crud_permissions": has_crud_permissions,
            "APP_BASE_URL": settings.APP_BASE_URL,
        },
    )


def component_details_public(request: HttpRequest, component_id: str) -> HttpResponse:
    try:
        component: Component = Component.objects.get(pk=component_id)
    except Component.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Component not found"))

    # Verify access to project
    if not component.is_public:
        return error_response(request, HttpResponseNotFound("Component not found"))

    sboms = SBOM.objects.filter(component_id=component_id).order_by("-created_at").all()

    branding_info = BrandingInfo(**component.team.branding_info)

    return render(
        request,
        "sboms/component_details_public.html",
        {"component": component, "sboms": sboms, "brand": branding_info},
    )


@login_required
def component_details_private(request: HttpRequest, component_id: str) -> HttpResponse:
    try:
        component: Component = Component.objects.get(pk=component_id)
    except Component.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Component not found"))

    # Verify access to project
    if not verify_item_access(request, component, ["guest", "owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for members of the team"))

    has_crud_permissions = verify_item_access(request, component, ["owner", "admin"])
    is_owner = verify_item_access(request, component, ["owner"])

    sboms = SBOM.objects.filter(component_id=component_id).order_by("-created_at").all()

    return render(
        request,
        "sboms/component_details_private.html",
        {
            "component": component,
            "has_crud_permissions": has_crud_permissions,
            "is_owner": is_owner,
            "sboms": sboms,
            "APP_BASE_URL": settings.APP_BASE_URL,
            "current_team": request.session.get("current_team", {}),
        },
    )


@login_required
def delete_component(request: HttpRequest, component_id: str) -> HttpResponse:
    try:
        component: Component = Component.objects.get(pk=component_id)
    except Component.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Component not found"))

    if not verify_item_access(request, component, ["owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for owners or admins of the component"))

    component.delete()

    messages.add_message(
        request,
        messages.INFO,
        f"Component {component.name} deleted",
    )

    return redirect("sboms:components_dashboard")


@login_required
def transfer_component_to_team(request: HttpRequest, component_id: str) -> HttpResponse:
    """
    Transfer component to a different team.

    User must have owner role in component's current team and owner or admin role in target team.
    """
    if request.method != "POST":
        return error_response(request, HttpResponseBadRequest("Invalid request"))

    team_key = request.POST.get("team_key")
    team_id = token_to_number(team_key)

    try:
        component = Component.objects.get(pk=component_id)
    except Component.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Component not found"))

    if not verify_item_access(request, component, ["owner"]):
        return error_response(request, HttpResponseForbidden("Only allowed for owners of the component"))

    target_team = request.session.get("user_teams", {}).get(team_key, {})
    if target_team.get("role", "") not in ("owner", "admin"):
        return error_response(request, HttpResponseForbidden("Only allowed for admins or owners of the target team"))

    with transaction.atomic():
        # Remove component's existing linkages to projects if any
        component.projects.clear()
        component.team_id = team_id
        component.save()

    messages.add_message(
        request,
        messages.INFO,
        f"Component {component.name} transferred to team {target_team.get('name')}",
    )

    return redirect("sboms:component_details", component_id=component_id)


def sbom_details_public(request: HttpRequest, sbom_id: str) -> HttpResponse:
    try:
        sbom: SBOM = SBOM.objects.get(pk=sbom_id)
    except SBOM.DoesNotExist:
        return error_response(request, HttpResponseNotFound("SBOM not found"))

    if not sbom.public_access_allowed:
        return error_response(request, HttpResponseNotFound("SBOM not found"))

    branding_info = BrandingInfo(**sbom.component.team.branding_info)

    return render(
        request,
        "sboms/sbom_details_public.html",
        {"sbom": sbom, "brand": branding_info},
    )


@login_required
def sbom_details_private(request: HttpRequest, sbom_id: str) -> HttpResponse:
    try:
        sbom: SBOM = SBOM.objects.get(pk=sbom_id)
    except SBOM.DoesNotExist:
        return error_response(request, HttpResponseNotFound("SBOM not found"))

    if not verify_item_access(request, sbom, ["guest", "owner", "admin"]):
        return error_response(request, HttpResponseForbidden("Only allowed for members of the team"))

    return render(
        request,
        "sboms/sbom_details_private.html",
        {"sbom": sbom, "APP_BASE_URL": settings.APP_BASE_URL},
    )


def sbom_download(request: HttpRequest, sbom_id: str) -> HttpResponse:
    try:
        sbom = SBOM.objects.get(pk=sbom_id)
    except SBOM.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Project not found"))

    if not sbom.public_access_allowed:
        if not verify_item_access(request, sbom, ["guest", "owner", "admin"]):
            return error_response(request, HttpResponseForbidden("Only allowed for members of the team"))

    if not sbom.sbom_filename:
        return error_response(request, HttpResponseBadRequest("SBOM file not found"))

    s3 = S3Client("SBOMS")
    sbom_data = s3.get_sbom_data(sbom.sbom_filename)
    response = HttpResponse(sbom_data, content_type="application/json")
    response["Content-Disposition"] = "attachment; filename=" + sbom.name

    return response


def sbom_download_project(request: HttpRequest, project_id: str) -> HttpResponse:
    """
    Download a zip file containing the SBOMs for all components in a project.
    """
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return error_response(request, HttpResponseNotFound("Project not found"))

    if not project.is_public:
        if not verify_item_access(request, project, ["guest", "owner", "admin"]):
            return error_response(request, HttpResponseForbidden("Only allowed for members of the team"))

    with tempfile.TemporaryDirectory() as temp_dir:
        sbom_zip_path = get_project_sbom_package(project, Path(temp_dir))

        response = HttpResponse(open(sbom_zip_path, "rb").read(), content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename={project.name}.cdx.zip"

        return response
