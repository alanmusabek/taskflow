from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import (
    CASCADE,
    PROTECT,
    SET_NULL,
    CharField,
    DateField,
    DateTimeField,
    ForeignKey,
    Index,
    Model,
    TextChoices,
    TextField,
)
from django.utils import timezone as django_timezone

from apps.teams.models import Membership


class TaskStatus(TextChoices):
    TODO = "to_do", "To Do"                   
    IN_PROGRESS = "in_progress", "In Progress"
    DONE = "done", "Done"


class TaskPriority(TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class Task(Model):
    """Individual work item that belongs to exactly one project."""

    TITLE_MAX_LEN = 200
    STATUS_MAX_LEN = 20
    PRIORITY_MAX_LEN = 10

    title = CharField(
        max_length=TITLE_MAX_LEN,
    )
    description = TextField(
        blank=True,
        default="",
    )
    project = ForeignKey(
        to="projects.Project",
        on_delete=CASCADE,                  
        related_name="tasks",
    )
    assignee = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=SET_NULL,                
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    created_by = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,                  
        related_name="created_tasks",
    )
    status = CharField(
        max_length=STATUS_MAX_LEN,
        choices=TaskStatus,
        default=TaskStatus.TODO,
    )
    priority = CharField(
        max_length=PRIORITY_MAX_LEN,
        choices=TaskPriority,
        default=TaskPriority.MEDIUM,
    )
    due_date = DateField(
        null=True,
        blank=True,
    )
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ("-created_at",)
        verbose_name = "task"
        verbose_name_plural = "tasks"
        get_latest_by = "created_at"
        indexes = [
            Index(fields=("project", "status"), name="task_project_status_idx"),
        ]

    def __str__(self) -> str:
        """How the object looks in the admin and in the shell."""
        return self.title

    def __is_project_participant(self, user_id: int) -> bool:
        """Check if the user is the project owner or a member of a project team."""

        if self.project.owner_id == user_id:
            return True

        return Membership.objects.filter(
            team__project=self.project,
            user_id=user_id,
        ).exists()

    def clean(self) -> None:
        """Python-level validation (called in forms / full_clean())."""

        errors: dict[str, str] = {}

        if self.due_date is not None:
            creation_date = (
                django_timezone.localdate(self.created_at)
                if self.created_at is not None
                else django_timezone.localdate()
            )
            if self.due_date < creation_date:
                errors["due_date"] = "Due date cannot be earlier than creation date."

        if self.project_id is not None:
            if (
                self.assignee_id is not None
                and not self.__is_project_participant(self.assignee_id)
            ):
                errors["assignee"] = (
                    "Assignee must be the project owner or a member of "
                    "a team in this project."
                )

            
            if (
                self.pk is None
                and self.created_by_id is not None
                and not self.__is_project_participant(self.created_by_id)
            ):
                errors["created_by"] = (
                    "The creator must be the project owner or a member of "
                    "a team in this project."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Validate the task before saving it (same idea as the delete() override)."""
        self.full_clean()
        super().save(*args, **kwargs)
