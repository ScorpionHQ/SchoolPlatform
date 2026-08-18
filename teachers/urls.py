from django.urls import path

from . import views

app_name = "teachers"

urlpatterns = [

    path(
        "",
        views.teacher_list,
        name="list",
    ),

    path(
        "dashboard/",
        views.teacher_dashboard,
        name="dashboard",
    ),

    path(
        "my-students/",
        views.my_students,
        name="my_students",
    ),

    path(
        "attendance/",
        views.take_attendance,
        name="take_attendance",
    ),

    path(
        "grades/",
        views.enter_grades,
        name="enter_grades",
    ),

    path(
        "create/",
        views.teacher_create,
        name="create",
    ),

    path(
        "<int:pk>/edit/",
        views.teacher_update,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.teacher_delete,
        name="delete",
    ),

]