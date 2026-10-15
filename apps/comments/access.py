"""Access rules for comments.

A user may work with comments of a task only if they take part in the
task's project: they are its owner or a member of one of its teams.
Editing and deleting is limited to the comment author or an administrator
(superuser, staff or the project owner).
"""

from django.db.models import Q

from apps.teams.models import Membership

from .models import Comment


def can_access_task(user, task) -> bool:
    """Can the user read and write comments on this task?"""
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if task.project.owner_id == user.pk:
        return True

    return Membership.objects.filter(
        team__project_id=task.project_id,
        user_id=user.pk,
    ).exists()


def is_comment_admin(user, task) -> bool:
    """Administrators may edit and delete other people's comments."""
    if not user.is_authenticated:
        return False

    return (
        user.is_superuser
        or user.is_staff
        or task.project.owner_id == user.pk
    )


def can_modify_comment(user, comment: Comment) -> bool:
    """Can the user edit or delete this comment?"""
    if not user.is_authenticated:
        return False

    if comment.author_id == user.pk:
        return True

    return is_comment_admin(user, comment.task)


def comments_visible_to(user):
    """Queryset of comments the user is allowed to see."""
    if not user.is_authenticated:
        return Comment.objects.none()

    queryset = Comment.objects.select_related("task", "author")

    if user.is_superuser:
        return queryset

    member_project_ids = Membership.objects.filter(
        user_id=user.pk,
    ).values("team__project_id")

    return queryset.filter(
        Q(task__project__owner_id=user.pk)
        | Q(task__project_id__in=member_project_ids)
    )
