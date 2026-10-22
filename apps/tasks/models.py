from typing import Any

from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
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

from .access import is_project_participant


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

    @classmethod
    def from_db(cls, db, field_names, values):
        """Remember the stored values so clean() can tell what changed."""
        instance = super().from_db(db, field_names, values)
        instance._loaded_due_date = instance.__dict__.get("due_date")
        instance._loaded_assignee_id = instance.__dict__.get("assignee_id")
        return instance

    def clean(self) -> None:
        """Python-level validation (called in forms / full_clean()).

        Rules that depend on "today" or on current team membership are only
        enforced when the relevant field is new or changed, so old tasks stay
        editable (e.g. marking an overdue task as done, or editing a task whose
        assignee has since left the project).
        """

        errors: dict[str, str] = {}
        is_new = self.pk is None

        due_date_changed = is_new or self.due_date != getattr(
            self, "_loaded_due_date", None
        )
        if self.due_date is not None and due_date_changed:
            creation_date = (
                django_timezone.localdate(self.created_at)
                if self.created_at is not None
                else django_timezone.localdate()
            )
            if self.due_date < creation_date:
                errors["due_date"] = "Due date cannot be earlier than creation date."

        if self.project_id is not None:
            assignee_changed = is_new or self.assignee_id != getattr(
                self, "_loaded_assignee_id", None
            )
            if (
                self.assignee_id is not None
                and assignee_changed
                and not is_project_participant(self.project, self.assignee_id)
            ):
                errors["assignee"] = (
                    "Assignee must be the project owner or a member of "
                    "a team in this project."
                )

            # created_by is not a form field, so this error is reported as a
            # non-field error. Superusers may create tasks in any project.
            if (
                is_new
                and self.created_by_id is not None
                and not self.created_by.is_superuser
                and not is_project_participant(self.project, self.created_by_id)
            ):
                errors[NON_FIELD_ERRORS] = (
                    "The creator must be the project owner or a member of "
                    "a team in this project."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Validate the task before saving it."""
        self.full_clean()
        super().save(*args, **kwargs)
        self._loaded_due_date = self.due_date
        self._loaded_assignee_id = self.assignee_id
