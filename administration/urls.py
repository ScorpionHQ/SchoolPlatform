from django.urls import path

from . import views

app_name = "administration"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "users/",
        views.user_list,
        name="user_list",
    ),
    path(
        "users/create/",
        views.user_create,
        name="user_create",
    ),
    path(
        "users/<int:pk>/edit/",
        views.user_update,
        name="user_update",
    ),
    path(
        "users/<int:pk>/delete/",
        views.user_delete,
        name="user_delete",
    ),
]
