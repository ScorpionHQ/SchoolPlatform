from django.urls import path
from . import views

app_name = "students"

urlpatterns = [

    path(
        "",
        views.student_list,
        name="list",
    ),

    path(
        "create/",
        views.student_create,
        name="create",
    ),

    path(
        "import/",
        views.student_import,
        name="import",
    ),

    path(
        "created/",
        views.student_created,
        name="created",
    ),

    path(
        "credentials/pdf/",
        views.student_credentials_pdf,
        name="credentials_pdf",
    ),

    path(
        "<int:pk>/update/",
        views.student_update,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.student_delete,
        name="delete",
    ),

    

    path(
        "subjects/",
        views.student_subjects,
        name="subjects",
    ),

    path(
        "grades/",
        views.student_grades,
        name="grades",
    ),

    path(
        "attendance/",
        views.student_attendance,
        name="attendance",
    ),

    path(
        "profile/",
        views.student_profile,
        name="profile",
    ),
]