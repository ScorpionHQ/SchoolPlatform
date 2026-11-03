from django.urls import path

from . import views

urlpatterns = [

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "change-password/",
        views.change_password_view,
        name="change_password",
    ),

    path(
        "password-reset/",
        views.password_reset_request,
        name="password_reset",
    ),

    path(
        "password-reset/<uidb64>/<token>/",
        views.SetNewPasswordView.as_view(),
        name="password_reset_confirm",
    ),

    path(
        "profile/",
        views.profile_view,
        name="profile",
    ),

    path(
        "upload-photo/",
        views.upload_profile_photo,
        name="upload_photo",
    ),

]