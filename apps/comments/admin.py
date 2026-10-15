from django.contrib import admin
from django.utils.text import Truncator

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task",
        "author",
        "short_content",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "task__project")
    search_fields = ("content", "author__email", "task__title")
    raw_id_fields = ("task", "author")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("task", "author")
    ordering = ("-created_at",)

    @admin.display(description="Content")
    def short_content(self, obj: Comment) -> str:
        return Truncator(obj.content).chars(60)
