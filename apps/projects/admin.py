
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "deadline",
        "created_at",
    )
    list_filter = ("status", "created_at", "deadline")
    search_fields = ("name", "description", "owner__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
