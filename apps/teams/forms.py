
from django import forms
from django.contrib.auth import get_user_model

from apps.projects.models import Project
from .models import Membership, Team

User = get_user_model()


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description", "project"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["project"].queryset = Project.objects.filter(
                owner=user
            )


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "role"]

    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team

    def clean_user(self):
        user = self.cleaned_data["user"]
        if self.team and Membership.objects.filter(
            team=self.team, user=user
        ).exists():
            raise forms.ValidationError(
                "This user is already a member of this team."
            )
        return user
