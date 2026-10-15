
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.projects.models import Project
from apps.teams.models import Membership

from .forms import TaskForm
from .models import Task


def is_project_member(user, project) -> bool:
    if not user.is_authenticated:
        return False

    if project.owner_id == user.pk:
        return True

    return Membership.objects.filter(
        team__project=project,
        user=user,
    ).exists()


def has_task_permission(user, permission: str) -> bool:
    return user.is_staff and user.has_perm(permission)


def get_accessible_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if (
        is_project_member(request.user, project)
        or has_task_permission(request.user, "tasks.view_task")
    ):
        return project

    raise PermissionDenied


def get_accessible_task(request, task_id):
    task = get_object_or_404(
        Task.objects.select_related("project", "assigned_to"),
        pk=task_id,
    )

    get_accessible_project(request, task.project_id)
    return task


def serialize_task(task) -> dict:
    return {
        "id": task.pk,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "assigned_to_id": task.assigned_to_id,
        "status": task.status,
        "priority": task.priority,
        "due_date": (
            task.due_date.isoformat()
            if task.due_date else None
        ),
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


@login_required
@require_http_methods(["GET"])
def task_list(request, project_id):
    project = get_accessible_project(request, project_id)

    tasks = Task.objects.filter(
        project=project
    ).order_by("-created_at")

    return JsonResponse({
        "project_id": project.pk,
        "tasks": [serialize_task(task) for task in tasks],
    })


@login_required
@require_http_methods(["GET"])
def task_detail(request, task_id):
    task = get_accessible_task(request, task_id)

    return JsonResponse(serialize_task(task))


@login_required
@require_http_methods(["POST"])
def task_create(request, project_id):
    project = get_accessible_project(request, project_id)

    if not (
        project.owner_id == request.user.pk
        or has_task_permission(request.user, "tasks.add_task")
    ):
        raise PermissionDenied

    form = TaskForm(request.POST, project=project)

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    task = form.save(commit=False)
    task.project = project
    task.save()

    return JsonResponse(serialize_task(task), status=201)


@login_required
@require_http_methods(["POST"])
def task_update(request, task_id):
    task = get_accessible_task(request, task_id)

    if not (
        task.project.owner_id == request.user.pk
        or has_task_permission(request.user, "tasks.change_task")
    ):
        raise PermissionDenied

    form = TaskForm(
        request.POST,
        instance=task,
        project=task.project,
    )

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    task = form.save()
    return JsonResponse(serialize_task(task))


@login_required
@require_http_methods(["POST"])
def task_update_status(request, task_id):
    task = get_accessible_task(request, task_id)

    if not (
        is_project_member(request.user, task.project)
        or has_task_permission(request.user, "tasks.change_task")
    ):
        raise PermissionDenied

    status = request.POST.get("status")

    if status not in Task.Status.values:
        return JsonResponse(
            {"error": "Invalid task status."},
            status=400,
        )

    task.status = status
    task.save()

    return JsonResponse(serialize_task(task))


@login_required
@require_http_methods(["POST"])
def task_delete(request, task_id):
    task = get_accessible_task(request, task_id)

    if not (
        task.project.owner_id == request.user.pk
        or has_task_permission(request.user, "tasks.delete_task")
    ):
        raise PermissionDenied

    task.delete()

    return JsonResponse({
        "message": "Task deleted successfully."
    })
