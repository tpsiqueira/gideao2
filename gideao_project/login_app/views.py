import requests
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from ldap3 import Server, Connection


def logout_view(request):
    logout(request)

    return redirect("login_app")


def login_ldap(request):
    mensagem = ""

    if request.method == "POST":
        username = request.POST.get("username", None).lower()
        password = request.POST.get("password", None)

        s = Server("ldap://petrobras.biz")
        c = Connection(s, user="%s@petrobras.biz" % username, password=password)

        if c.bind():
            try:
                user = User.objects.get(username=username)
                login(request, user)
                return redirect("Home")
            except User.DoesNotExist:
                user = User.objects.create_user(username=username)
                login(request, user)
                return redirect("Home")
        else:
            mensagem = "Credencial inválida."

    return render(request, "login_app/login.html", {"mensagem": mensagem})
