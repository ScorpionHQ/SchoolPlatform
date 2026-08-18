from django.urls import include, path

from . import views

handler400 = "core.views.error_400"
handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"

urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "service-worker.js",
        views.service_worker,
        name="service_worker",
    ),

    path(
        "student-dashboard/",
        views.student_dashboard,
        name="student_dashboard",
    ),

    path(
        "parent-dashboard/",
        views.parent_dashboard,
        name="parent_dashboard",
    ),

    path(
        "parent-children/",
        views.parent_children,
        name="parent_children",
    ),

    path(
        "parent-grades/",
        views.parent_grades,
        name="parent_grades",
    ),

    path(
        "parent-attendance/",
        views.parent_attendance,
        name="parent_attendance",
    ),

    path(
        "manager-dashboard/",
        views.manager_dashboard,
        name="manager_dashboard",
    ),

    path(
        "manager-teachers/",
        views.manager_teachers,
        name="manager_teachers",
    ),

    path(
        "manager-students/",
        views.manager_students,
        name="manager_students",
    ),

    path("institutions/", include("institutions.urls")),
    path("students/", include("students.urls")),
    path("classes/", include("classes.urls")),
    path("teachers/", include("teachers.urls")),
    path("subjects/", include("subjects.urls")),
    path("attendance/", include("attendance.urls")),
    path("parents/", include("parents.urls")),
    path("grades/", include("grades.urls")),

]