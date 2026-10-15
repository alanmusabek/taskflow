
from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("", views.team_list, name="team_list"),
    path("create/", views.team_create, name="team_create"),
    path("<int:team_id>/", views.team_detail, name="team_detail"),
    path("<int:team_id>/edit/", views.team_update, name="team_update"),
    path("<int:team_id>/delete/", views.team_delete, name="team_delete"),
    path(
        "<int:team_id>/members/add/",
        views.member_add,
        name="member_add",
    ),
    path(
        "<int:team_id>/members/<int:membership_id>/remove/",
        views.member_remove,
        name="member_remove",
    ),
    path(
        "<int:team_id>/members/<int:membership_id>/role/",
        views.member_update_role,
        name="member_update_role",
    ),
]
