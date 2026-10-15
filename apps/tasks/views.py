from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.projects.models import Project
from apps.teams.models import Membership

from .forms import TaskForm
from .models import Task, TaskPriority, TaskStatus



def _can_access_project(user, project) -> bool:
    """Owner, superuser or a member of one of the project's teams."""
    if user.is_superuser or project.owner_id == user.pk:
        return True

    return Membership.objects.filter(
        team__project=project,
        user=user,
    ).exists()


def _can_manage_task(user, task) -> bool:
    """Edit/delete: creator, assignee, project owner or superuser."""
    return (
        user.is_superuser
        or task.project.owner_id == user.pk
        or task.created_by_id == user.pk
        or task.assignee_id == user.pk
    )


def _get_project_for_user(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)

    if not _can_access_project(request.user, project):
        raise PermissionDenied

    return project


def _get_task_for_user(request, pk, manage=False):
    task = get_object_or_404(
        Task.objects.select_related("project", "assignee", "created_by"),
        pk=pk,
    )

    if not _can_access_project(request.user, task.project):
        raise PermissionDenied

    if manage and not _can_manage_task(request.user, task):
        raise PermissionDenied

    return task


@login_required
def my_tasks(request):
    """Tasks assigned to the current user."""
    tasks = Task.objects.filter(assignee=request.user).select_related("project")

    status = request.GET.get("status")
    if status in TaskStatus.values:
        tasks = tasks.filter(status=status)

    return render(
        request,
        "tasks/my_tasks.html",
        {
            "tasks": tasks,
            "statuses": TaskStatus.choices,
            "current_status": status,
        },
    )


@login_required
def task_list(request, project_pk):
    """All tasks of a project with optional filters (?status=&priority=&q=)."""
    project = _get_project_for_user(request, project_pk)

    tasks = project.tasks.select_related("assignee")

    status = request.GET.get("status")
    if status in TaskStatus.values:
        tasks = tasks.filter(status=status)

    priority = request.GET.get("priority")
    if priority in TaskPriority.values:
        tasks = tasks.filter(priority=priority)

    query = request.GET.get("q", "").strip()
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    return render(
        request,
        "tasks/task_list.html",
        {
            "project": project,
            "tasks": tasks,
            "statuses": TaskStatus.choices,
            "priorities": TaskPriority.choices,
            "current_status": status,
            "current_priority": priority,
            "query": query,
        },
    )


@login_required
def task_create(request, project_pk):
    project = _get_project_for_user(request, project_pk)

    # Project and creator are set before validation so Task.clean()
    # can check the assignee / creator against the project.
    task = Task(project=project, created_by=request.user)
    form = TaskForm(request.POST or None, instance=task, project=project)

    if request.method == "POST" and form.is_valid():
        task = form.save()
        return redirect("tasks:detail", pk=task.pk)

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "project": project,
            "page_title": "Create task",
        },
    )


@login_required
def task_detail(request, pk):
    task = _get_task_for_user(request, pk)

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "can_manage": _can_manage_task(request.user, task),
        },
    )


@login_required
def task_update(request, pk):
    task = _get_task_for_user(request, pk, manage=True)

    form = TaskForm(
        request.POST or None,
        instance=task,
        project=task.project,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("tasks:detail", pk=task.pk)

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "task": task,
            "project": task.project,
            "page_title": "Edit task",
        },
    )


@login_required
def task_delete(request, pk):
    task = _get_task_for_user(request, pk, manage=True)
    project_pk = task.project_id

    if request.method == "POST":
        task.delete()
        return redirect("tasks:list", project_pk=project_pk)

    return render(
        request,
        "tasks/task_confirm_delete.html",
        {"task": task},
    )