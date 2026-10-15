from django.contrib.admin import ModelAdmin, register
from django.core.handlers.wsgi import WSGIRequest

from apps.tasks.forms import TaskAdminForm
from apps.tasks.models import Task


@register(Task)
class TaskAdmin(ModelAdmin):
    """Task admin class configuration."""

    form = TaskAdminForm

    list_display = (
        "id",
        "title",
        "project",
        "assignee",
        "status",
        "priority",
        "due_date",
        "created_by",
    )
    list_display_links = (
        "id",
        "title",
    )
    list_filter = (
        "status",
        "priority",
        "project",
        "due_date",
    )
    search_fields = (
        "id",
        "title",
        "description",
    )
    list_per_page = 50
    save_on_top = True
    fieldsets = (
        (
            "General information",
            {
                "fields": (
                    "id",
                    "title",
                    "description",
                    "project",
                    "created_by",
                )
            },
        ),
        (
            "Progress",
            {
                "fields": (
                    ("status", "priority"),
                    "assignee",
                    "due_date",
                )
            },
        ),
        (
            "Date and time information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(self, request: WSGIRequest, obj: Task | None = None) -> tuple[str, ...]:
        """The project and the creator of an existing task cannot be changed."""

        if obj:     
            return (
                "project",
                "created_by",
            ) + self.readonly_fields
        return self.readonly_fields    
