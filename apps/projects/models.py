
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = "Planning", "Planning"
        ACTIVE = "Active", "Active"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="projects",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PLANNING,
    )

    deadline = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self) -> None:
        super().clean()

        creation_date = (
            timezone.localdate(self.created_at)
            if self.created_at is not None
            else timezone.localdate()
        )

        if self.deadline is not None and self.deadline < creation_date:
            raise ValidationError(
                {
                    "deadline": (
                        "Deadline cannot be earlier than creation date."
                    )
                }
            )
    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
