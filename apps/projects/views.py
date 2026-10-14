
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import Project




@login_required
def project_list(request):
    if (
        request.user.is_staff
        and request.user.has_perm("projects.view_project")
    ):
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(owner=request.user)

    projects = projects.order_by("-created_at")

    return render(
        request,
        "projects/project_list.html",
        {"projects": projects},
    )



def _get_project_for_user(request, pk, permission):
    project = get_object_or_404(Project, pk=pk)

    if project.owner_id == request.user.pk:
        return project

    if (
        request.user.is_staff
        and request.user.has_perm(permission)
    ):
        return project

    raise PermissionDenied



@login_required
def project_detail(request, pk):
    project = _get_project_for_user(
        request,
        pk,
        "projects.view_project",
    )

    return render(
        request,
        "projects/project_detail.html",
        {"project": project},
    )


@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()

        return redirect("projects:detail", pk=project.pk)

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "page_title": "Create project",
        },
    )


@login_required
def project_update(request, pk):
    project = _get_project_for_user(
        request,
        pk,
        "projects.change_project",
    )

    form = ProjectForm(
        request.POST or None,
        instance=project,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("projects:detail", pk=project.pk)

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "project": project,
            "page_title": "Edit project",
        },
    )


@login_required
def project_delete(request, pk):
    project = _get_project_for_user(
        request,
        pk,
        "projects.delete_project",
    )

    if request.method == "POST":
        project.delete()
        return redirect("projects:list")

    return render(
        request,
        "projects/project_confirm_delete.html",
        {"project": project},
    )
