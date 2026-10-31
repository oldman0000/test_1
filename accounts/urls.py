from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.enter_email, name="enter_email"),
    path("login/code/", views.enter_code, name="enter_code"),
    path("login/username/", views.choose_username, name="choose_username"),
    path("logout/", views.log_out, name="logout"),
    path("account/username/", views.change_username, name="change_username"),
    path("account/photo/", views.change_photo, name="change_photo"),
    path("avatar/<int:user_id>/", views.avatar, name="avatar"),
]