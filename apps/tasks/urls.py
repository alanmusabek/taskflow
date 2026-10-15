from django.urls import path

from . import views


app_name = "tasks"

urlpatterns = [
    path("", views.my_tasks, name="mine"),
    path("project/<int:project_pk>/", views.task_list, name="list"),
    path("project/<int:project_pk>/create/", views.task_create, name="create"),
    path("<int:pk>/", views.task_detail, name="detail"),
    path("<int:pk>/edit/", views.task_update, name="update"),
    path("<int:pk>/delete/", views.task_delete, name="delete"),
]
