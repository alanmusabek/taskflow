from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from .models import Membership, Team


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "members_count", "created_at")
    list_filter = ("project",)
    search_fields = ("name", "project__name")
    date_hierarchy = "created_at"
    inlines = [MembershipInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        queryset = super().get_queryset(request).annotate(
            _members=Count("membership")
        )
        if request.user.is_superuser:
            return queryset
        return queryset.filter(project__owner=request.user)

    @admin.display(description="Members", ordering="_members")
    def members_count(self, obj: Team) -> int:
        return obj._members


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "role", "joined_at")
    list_filter = ("role", "team__project")
    search_fields = ("user__email", "team__name")
    date_hierarchy = "joined_at"

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(team__project__owner=request.user)