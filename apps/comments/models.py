from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Comment(models.Model):
    """A discussion message attached to a task."""

    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comments",
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
        ]

    def clean(self) -> None:
        super().clean()

        if self.content is not None:
            self.content = self.content.strip()

        if not self.content:
            raise ValidationError({"content": "Comment cannot be empty."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Comment #{self.pk} by {self.author_id} on task {self.task_id}"
