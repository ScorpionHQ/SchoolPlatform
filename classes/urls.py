from django.urls import path

from . import views

app_name = "classes"

urlpatterns = [

    path(
        "",
        views.classroom_list,
        name="list",
    ),

    path(
        "create/",
        views.classroom_create,
        name="create",
    ),

    path(
        "<int:pk>/edit/",
        views.classroom_update,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.classroom_delete,
        name="delete",
    ),

]