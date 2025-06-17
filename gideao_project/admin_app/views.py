from __future__ import unicode_literals
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from admin_app.models import uo, ativo, uep, poco
import json
from django.core import serializers
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from admin_app.models import (
    uo,
    ativo,
    uep,
    poco,
    variavel_industrial,
    grandeza_industrial,
    grandeza_especialista,
)


@login_required()
def home(request):
    nome = request.user.username
    grupos = request.user.groups.values_list("name", flat=True)
    usuarios = json.dumps(serializers.serialize("json", User.objects.all()))
    uos = json.dumps(serializers.serialize("json", uo.objects.all()))
    ativos = json.dumps(serializers.serialize("json", ativo.objects.all()))
    ueps = json.dumps(serializers.serialize("json", uep.objects.all()))
    pocos = json.dumps(serializers.serialize("json", poco.objects.all()))
    return render(
        request,
        "base.html",
        {
            "usuario": nome,
            "usuarios": usuarios,
            "uos": uos,
            "ativos": ativos,
            "ueps": ueps,
            "pocos": pocos,
        },
    )

@login_required()
@transaction.atomic
def ajax_adicionar_uo(request): # Adiciona uma nova UO via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.add_uo") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            new_uo = uo(nome=request.POST["nome"])
            print("novo objeto uo:", new_uo)
            new_uo.save()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    uos = json.dumps(serializers.serialize("json", uo.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["uos"] = uos
    return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_editar_uo(request): # Edita os dados de uma UO via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.edit_uo") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            uo_sel = uo.objects.get(id=int(request.POST["pk"]))
            print("novo objeto uo:", uo_sel)
            uo_sel.nome = request.POST["nome"]
            uo_sel.save()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    uos = json.dumps(serializers.serialize("json", uo.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["uos"] = uos
    return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_excluir_uo(request): # Exclui uma UO existente via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.delete_uo") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            uo_sel = uo.objects.get(id=int(request.POST["pk"]))
            uo_sel.delete()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    uos = json.dumps(serializers.serialize("json", uo.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["uos"] = uos
    return HttpResponse(json.dumps(saida), content_type="application/json")


# ATIVOS DE PRODUÇÃO
@login_required()
@transaction.atomic
def ajax_adicionar_ativo(request): # Adiciona um novo ativo via AJAX.
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.add_ativo") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            new_ativo = ativo(uo_id=int(request.POST["uo"]), nome=request.POST["nome"])
            print("novo objeto ativo:", new_ativo)
            new_ativo.save()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    ativos = json.dumps(serializers.serialize("json", ativo.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["ativos"] = ativos
    return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_editar_ativo(request): # Edita os dados de um ativo via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.edit_ativo") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            ativo_sel = ativo.objects.get(id=int(request.POST["pk"]))
            print("objeto selecioando ativo:", ativo_sel)
            ativo_sel.nome = request.POST["nome"]
            ativo_sel.save()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    ativos = json.dumps(serializers.serialize("json", ativo.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["ativos"] = ativos
    return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_excluir_ativo(request): # Exclui um ativo existente via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.delete_ativo") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            ativo_sel = ativo.objects.get(id=int(request.POST["pk"]))
            ativo_sel.delete()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    ativos = json.dumps(serializers.serialize("json", ativo.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["ativos"] = ativos
    return HttpResponse(json.dumps(saida), content_type="application/json")


# UEPs
@login_required()
@transaction.atomic
def ajax_adicionar_uep(request): # Adiciona uma nova UEP via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.add_uep") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            new_uep = uep(
                ativo_id=int(request.POST["ativo"]), nome=request.POST["nome"]
            )
            print("novo objeto uep:", new_uep)
            new_uep.save()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    ueps = json.dumps(serializers.serialize("json", uep.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["ueps"] = ueps
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_editar_uep(request): # Edita os dados de uma UEP via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.edit_uep") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            uep_sel = uep.objects.get(id=int(request.POST["pk"]))
            print("objeto selecioando uep:", uep_sel)
            uep_sel.nome = request.POST["nome"]
            uep_sel.save()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    ueps = json.dumps(serializers.serialize("json", uep.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["ueps"] = ueps
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_excluir_uep(request): # Exclui uma UEP via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.delete_uep") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            uep_sel = uep.objects.get(id=int(request.POST["pk"]))
            uep_sel.delete()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    ueps = json.dumps(serializers.serialize("json", uep.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["ueps"] = ueps
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_adicionar_poco(request): # Adiciona um novo poço via AJAX.
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.add_poco") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            new_poco = poco(
                nome=str(request.POST["nome"]),
                uep_id=int(request.POST["uep"]),
            )
            new_poco.save()
            sucesso = True
        except:
            sucesso = False
    pocos = json.dumps(serializers.serialize("json", poco.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["pocos"] = pocos
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_editar_poco(request): # Edita os dados de um poço via AJAX
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.edit_poco") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            poco_sel = poco.objects.get(id=int(request.POST["pk"]))
            poco_sel.nome = str(request.POST["nome"])
            poco_sel.uep_id = int(request.POST["uep"])
            poco_sel.save()
            sucesso = True
        except:
            sucesso = False
    pocos = json.dumps(serializers.serialize("json", poco.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["pocos"] = pocos
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_excluir_poco(request): # Exclui um poço existente via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.delete_poco") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            poco_sel = poco.objects.get(id=int(request.POST["pk"]))
            poco_sel.delete()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    pocos = json.dumps(serializers.serialize("json", poco.objects.all()))
    saida = {}
    saida["sucesso"] = sucesso
    saida["pocos"] = pocos
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_adicionar_variavel_industrial(request): # Adiciona uma nova variável industrial via AJAX
    print(request)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.add_poco") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        print("entrou")
        try:
            new_variavel = variavel_industrial(
                nome=str(request.POST["nome"]),
                poco_id=int(request.POST["poco"]),
                grandeza_industrial_id=int(request.POST["grandeza_industrial"]),
                servidor_pi=str(request.POST["servidor_pi"]),
                tag=str(request.POST["tag"]),
                unidade_medida="",
            )
            new_variavel.save()
            sucesso = True
        except:
            sucesso = False
    variaveis_industriais = json.dumps(
        serializers.serialize(
            "json", variavel_industrial.objects.filter(poco=int(request.POST["poco"]))
        )
    )
    saida = {}
    saida["sucesso"] = sucesso
    saida["variaveis_industriais"] = variaveis_industriais
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_editar_variavel_industrial(request): # Edita os dados de uma variável industrial via AJAX
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.edit_poco") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            variavel_sel = variavel_industrial.objects.get(id=int(request.POST["pk"]))
            variavel_sel.nome = str(request.POST["nome"])
            variavel_sel.poco = poco.objects.get(id=int(request.POST["poco"]))
            variavel_sel.grandeza_industrial = grandeza_industrial.objects.get(
                id=int(request.POST["grandeza_industrial"])
            )
            variavel_sel.servidor_pi = str(request.POST["servidor_pi"])
            variavel_sel.tag = str(request.POST["tag"])
            variavel_sel.save()
            sucesso = True
        except:
            sucesso = False
    variaveis_industriais = json.dumps(
        serializers.serialize(
            "json",
            variavel_industrial.objects.filter(
                poco=poco.objects.get(id=int(request.POST["poco"]))
            ),
        )
    )
    saida = {}
    saida["sucesso"] = sucesso
    saida["variaveis_industriais"] = variaveis_industriais
    return HttpResponse(json.dumps(saida), content_type="application/json")


@login_required()
@transaction.atomic
def ajax_excluir_variavel_industrial(request): # Exclui uma variável industrial existente via AJAX
    print("requisição", request.POST)
    autorizacao = False
    sucesso = False
    if request.user.has_perm("gideao_project.admin_app.delete_poco") == True:
        autorizacao = True
    else:
        autorizacao = False
    if request.method == "POST" and autorizacao == True:
        try:
            variavel_sel = variavel_industrial.objects.get(id=int(request.POST["pk"]))
            poco_sel = variavel_sel.poco
            variavel_sel.delete()
            sucesso = True
        except:
            sucesso = False
    print("autorização", autorizacao, "sucesso", sucesso)
    variaveis_industriais = json.dumps(
        serializers.serialize("json", poco.objects.filter(poco=poco_sel))
    )
    saida = {}
    saida["sucesso"] = sucesso
    saida["variaveis_industriais"] = variaveis_industriais
    return HttpResponse(json.dumps(saida), content_type="application/json")
