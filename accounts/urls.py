from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.enter_email, name="enter_email"),
    path("login/code/", views.enter_code, name="enter_code"),
    path("login/username/", views.choose_username, name="choose_username"),
    path("logout/", views.log_out, name="logout"),
]



