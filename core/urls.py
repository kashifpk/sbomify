from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("settings", views.user_settings, name="settings"),
    path("access_tokens/<token_id>/delete", views.delete_access_token, name="delete_access_token"),
    path("logout", views.logout, name="logout"),
]
