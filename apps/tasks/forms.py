from django.forms import ModelForm, Textarea, TextInput

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
