from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("", views.chat_page, name="chat"),
    path("api/chat/", views.api_chat, name="api_chat"),
    path("api/files/upload/", views.api_files_upload, name="api_files_upload"),
    path("api/files/analyze/", views.api_files_analyze, name="api_files_analyze"),
    path("api/files/report/", views.api_files_report, name="api_files_report"),
]
