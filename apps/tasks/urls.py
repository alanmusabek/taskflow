from django.urls import path

from . import views


app_name = "tasks"

urlpatterns = [
    path(
        "projects/<int:project_id>/",
        views.task_list,
        name="list",
    ),
    path(
        "projects/<int:project_id>/create/",
        views.task_create,
        name="create",
    ),
    path(
        "<int:task_id>/",
        views.task_detail,
        name="detail",
    ),
    path(
        "<int:task_id>/edit/",
        views.task_update,
        name="update",
    ),
    path(
        "<int:task_id>/status/",
        views.task_update_status,
        name="update-status",
    ),
    path(
        "<int:task_id>/delete/",
        views.task_delete,
        name="delete",
    ),
]