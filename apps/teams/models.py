from django.conf import settings
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "name")

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    ROLE_CHOICES = [
        ("member", "Member"),
        ("lead", "Team Lead"),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default="member"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "user")

    def __str__(self) -> str:
        return f"{self.user} in {self.team}"