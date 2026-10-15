from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.teams.models import Membership

from .models import Task


User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "assigned_to",
            "status",
            "priority",
            "due_date",
        )

        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
            "due_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.project = project

        if project is not None:
            self.instance.project = project

            self.fields["assigned_to"].queryset = (
                User.objects.filter(
                    Q(pk=project.owner_id)
                    | Q(membership__team__project=project)
                )
                .distinct()
            )
        else:
            self.fields["assigned_to"].queryset = (
                User.objects.none()
            )