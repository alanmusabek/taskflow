from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import DateInput, ModelForm, Textarea, TextInput

from apps.tasks.models import Task


class TaskAdminForm(ModelForm):
    """Task form for the admin panel."""

    class Meta:
        model = Task
        fields = "__all__"
        widgets = {
            "title": TextInput(attrs={"placeholder": "e.g. Implement Authentication"}),
            "description": Textarea(attrs={"rows": 3}),
        }
        labels = {
            "due_date": "Deadline",
        }

    def clean_title(self) -> str:
        """Check one field: the title."""
        title: str = self.cleaned_data["title"]
        if len(title) < 3:
            raise ValidationError("Title must have at least 3 characters.")
        return title

    def clean(self) -> dict[str, Any]:
        """Check several fields together."""
        cleaned_data: dict[str, Any] = super().clean()
        if cleaned_data.get("status") == "done" and not cleaned_data.get("assignee"):
            self.add_error("assignee", "A finished task must have an assignee.")
        return cleaned_data


class TaskForm(ModelForm):
    """Task form for regular users (create / edit inside a project)."""

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        if project is not None:
            # Same rule as Task.clean(): owner or member of a project team.
            self.fields["assignee"].queryset = (
                get_user_model()
                .objects.filter(
                    Q(pk=project.owner_id)
                    | Q(membership__team__project=project)
                )
                .distinct()
            )

    class Meta:
        model = Task
        fields = ("title", "description", "assignee", "status", "priority", "due_date")
        widgets = {
            "title": TextInput(attrs={"class": "form-control"}),
            "description": Textarea(attrs={"class": "form-control", "rows": 4}),
            "due_date": DateInput(attrs={"class": "form-control", "type": "date"}),
        }
