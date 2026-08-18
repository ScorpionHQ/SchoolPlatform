from django.urls import path

from . import views

app_name = "institutions"

urlpatterns = [

    path(
        "",
        views.institution_list,
        name="list",
    ),

    path(
        "select/",
        views.institution_select,
        name="select",
    ),

    path(
        "switch/",
        views.institution_switch,
        name="switch",
    ),

    path(
        "create/",
        views.institution_create,
        name="create",
    ),
path(
    "<int:pk>/edit/",
    views.institution_update,
    name="update",
),
path(
    "<int:pk>/delete/",
    views.institution_delete,
    name="delete",
),
]
