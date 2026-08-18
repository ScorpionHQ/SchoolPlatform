from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [

    path(
        "",
        views.attendance_list,
        name="list",
    ),

    path(
        "calendar/",
        views.attendance_calendar,
        name="calendar",
    ),

    path(
        "create/",
        views.attendance_create,
        name="create",
    ),

    path(
      "session/",
       views.attendance_session,
       name="session",
    ),

    path(
        "<int:pk>/edit/",
        views.attendance_update,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.attendance_delete,
        name="delete",
    ),

]