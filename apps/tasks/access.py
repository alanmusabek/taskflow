"""Single source of truth for who may see and manage tasks."""

from apps.teams.models import Membership


def is_project_participant(project, user_id: int) -> bool:
    """The user owns the project or belongs to one of its teams."""
    if project.owner_id == user_id:
        return True

    return Membership.objects.filter(
        team__project=project,
        user_id=user_id,
    ).exists()


def can_access_project(user, project) -> bool:
    """Owner, superuser or a member of one of the project's teams."""
    if user.is_superuser:
        return True

    return is_project_participant(project, user.pk)


def can_manage_task(user, task) -> bool:
    """Edit/delete: creator, assignee, project owner or superuser."""
    return (
        user.is_superuser
        or task.project.owner_id == user.pk
        or task.created_by_id == user.pk
        or task.assignee_id == user.pk
    )
