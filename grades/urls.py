from django.urls import path

from . import views

app_name = "grades"

urlpatterns = [

    path(
        "",
        views.grade_list,
        name="list",
    ),

    path(
        "create/",
        views.grade_create,
        name="create",
    ),

    path(
        "<int:pk>/edit/",
        views.grade_update,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.grade_delete,
        name="delete",
    ),

]