from django.urls import path

from .views import (
    login_view,
    logout_view,
    profile_view,
    register,
    update_profile_view,
)

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("me/", profile_view, name="profile"),
    path("me/update/", update_profile_view, name="profile-update"),
]
