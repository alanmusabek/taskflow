from django.forms import DateInput, ModelForm, Textarea, TextInput
from django.contrib.auth import get_user_model
from django.db.models import Q
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


class TaskForm(ModelForm):
    """Task form for regular users (create / edit inside a project)."""

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        if project is not None:
            from django.contrib.auth import get_user_model
            from django.db.models import Q

            self.fields["assignee"].queryset = get_user_model().objects.filter(
                Q(pk=project.owner_id)
                | Q(membership__team__project=project)
            ).distinct()

    class Meta:
        model = Task
        fields = ("title", "description", "assignee", "status", "priority", "due_date")
        widgets = {
            "title": TextInput(attrs={"class": "form-control"}),
            "description": Textarea(attrs={"class": "form-control", "rows": 4}),
            "due_date": DateInput(attrs={"class": "form-control", "type": "date"}),
        }