from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.tasks.models import Task

from .access import can_access_task, can_modify_comment
from .forms import CommentForm
from .models import Comment


def _get_task_for_user(request, task_pk) -> Task:
    task = get_object_or_404(
        Task.objects.select_related("project"),
        pk=task_pk,
    )

    if not can_access_task(request.user, task):
        raise PermissionDenied

    return task


def _get_comment_for_user(request, pk) -> Comment:
    """Comment that the current user is allowed to edit or delete."""
    comment = get_object_or_404(
        Comment.objects.select_related("task__project", "author"),
        pk=pk,
    )

    if not can_modify_comment(request.user, comment):
        raise PermissionDenied

    return comment


def _back_to_task(task_pk):
    response = redirect("tasks:detail", pk=task_pk)
    response["Location"] += "#comments"
    return response


@login_required
def comment_list(request, task_pk):
    """All comments of a task (only for project participants)."""
    task = _get_task_for_user(request, task_pk)

    comments = task.comments.select_related("author")

    return render(
        request,
        "comments/comment_list.html",
        {
            "task": task,
            "comments": comments,
            "form": CommentForm(),
        },
    )


@login_required
def comment_create(request, task_pk):
    task = _get_task_for_user(request, task_pk)

    # Task and author are set before validation, like in tasks.views.
    comment = Comment(task=task, author=request.user)
    form = CommentForm(request.POST or None, instance=comment)

    if request.method == "POST" and form.is_valid():
        form.save()
        return _back_to_task(task.pk)

    return render(
        request,
        "comments/comment_form.html",
        {
            "form": form,
            "task": task,
            "page_title": "Add comment",
        },
    )


@login_required
def comment_update(request, pk):
    comment = _get_comment_for_user(request, pk)

    form = CommentForm(request.POST or None, instance=comment)

    if request.method == "POST" and form.is_valid():
        form.save()
        return _back_to_task(comment.task_id)

    return render(
        request,
        "comments/comment_form.html",
        {
            "form": form,
            "task": comment.task,
            "comment": comment,
            "page_title": "Edit comment",
        },
    )


@login_required
def comment_delete(request, pk):
    comment = _get_comment_for_user(request, pk)
    task_pk = comment.task_id

    if request.method == "POST":
        comment.delete()
        return _back_to_task(task_pk)

    return render(
        request,
        "comments/comment_confirm_delete.html",
        {"comment": comment, "task": comment.task},
    )
