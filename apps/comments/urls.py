from django.urls import path

from . import views


app_name = "comments"

urlpatterns = [
    path("task/<int:task_pk>/", views.comment_list, name="list"),
    path("task/<int:task_pk>/add/", views.comment_create, name="create"),
    path("<int:pk>/edit/", views.comment_update, name="update"),
    path("<int:pk>/delete/", views.comment_delete, name="delete"),
]
