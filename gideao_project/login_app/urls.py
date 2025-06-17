from django.urls import path
from . import views

urlpatterns = [path("", views.login_ldap, name="login_app")]
