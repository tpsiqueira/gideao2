from __future__ import unicode_literals

import requests
import json
import os
import sys
import datetime

from monitor_app.services.rtomongoservice import get_rto_data

import django
from admin_app.models import ativo_perf, poco_perf, uep, uo_perf
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from django.db import transaction

from requests.auth import HTTPBasicAuth

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gideao_project.settings")
django.setup()
import sys

from admin_app.models import (
    grandeza_especialista_perf,
    grandeza_industrial_perf,
    relacao_especialista_industrial_perf,
    variavel_industrial_perf,
    unidade_medida,
    
)

from monitor_app.models import amostra_perf, analise_perf, servidor_perf, sonda_perf

from django.core import serializers
from django.http import HttpResponse


@login_required()
def rotulagem_perf(request, uo="", ativo="", poco="", inicio="", fim=""):
    usuario = request.user.username
    usuarios = json.dumps(serializers.serialize("json", User.objects.all()))
    uos = json.dumps(serializers.serialize("json", uo_perf.objects.all().order_by("nome")))
    ativos = json.dumps(serializers.serialize("json", ativo_perf.objects.all().order_by("nome")))
    
    grandezas_industriais = json.dumps(
        serializers.serialize("json", grandeza_industrial_perf.objects.all())
    )
    grandezas_especialistas = json.dumps(
        serializers.serialize(
            "json", grandeza_especialista_perf.objects.all().order_by("nome")
        )
    )
    relacoes = json.dumps(
        serializers.serialize("json", relacao_especialista_industrial_perf.objects.all())
    )
    
    ueps = json.dumps(serializers.serialize("json", []))
      
    pocos = json.dumps(
        serializers.serialize("json", poco_perf.objects.all().order_by("nome"))
    )
      
    return render(
        request,
        "monitor/tela_rotulagem.html",
        {
            "usuarios": usuarios,
            "usuario": usuario,
            "uos": uos,
            "ativos": ativos,
            "pocos": pocos,
            "ueps": ueps,
            "grandezas_industriais": grandezas_industriais,
            "grandezas_especialistas": grandezas_especialistas,
            "relacoes": relacoes,
        },
    )

@login_required()    
def pocos_perf(request):
  ativo_id = int(request.GET['ativo'])    
  pocos = json.dumps(
    serializers.serialize("json", poco_perf.objects.filter(ativo_id=ativo_id).order_by("nome"))
  )
  return HttpResponse(pocos, content_type="application/json")

@login_required()
def ajax_carregar_instancia_por_ge_perf(request):
  # print("aqui tb")
  if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
      try:
          lista_analises = analise_perf.objects.filter(
              grandeza_especialista=int(request.POST["grandeza_especialista"])
          )
          saida = {}
          saida["analises"] = serializers.serialize("json", lista_analises)
          saida["saida"] = True
      except:
          saida = {}
          saida["analises"] = ""
          saida["saida"] = False
      return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()    
def ajax_carregar_instancias_perf(request):
    # print("Em carrega analises")
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            lista_analises = analise_perf.objects.all()
            saida = {}
            saida["analises"] = serializers.serialize("json", lista_analises)
            saida["saida"] = True
        except:
            saida = {}
            saida["analises"] = ""
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
def ajax_carregar_amostras_por_instancia_perf(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            lista_amostras = amostra_perf.objects.filter(
                analise=int(request.POST["analise"])
            ).order_by("inicio")
            saida = {}
            saida["amostras"] = serializers.serialize("json", lista_amostras)
            saida["saida"] = True
        except:
            saida = {}
            saida["amostras"] = ""
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic  
def ajax_excluir_instancia_por_id_perf(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            pk = request.POST["pk"]
            analise_sel = analise_perf.objects.filter(id=int(pk))[0]
            analise_sel.delete()
            saida = {}
            saida["saida"] = True
        except:
            saida = {}
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()      
def ajax_selecionar_ge_amostra_especialista_perf(request):
    # print("entrou em sgeamostraespec: ", request)
    # print(request.is_ajax(), request.POST)
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            poco_sel = poco_perf.objects.filter(id=int(request.POST["poco"]))
            ge_sel = grandeza_especialista_perf.objects.filter(
                id=int(request.POST["grandeza_especialista"])
            )

            grandezas_industriais_rel = relacao_especialista_industrial_perf.objects.filter(
                especialista=ge_sel[0]
            )

            variaveis_industriais_sel = []
            for item in grandezas_industriais_rel:
                variaveis_industriais_sel.append(
                    variavel_industrial_perf.objects.filter(poco=poco_sel[0]).filter(
                        grandeza_industrial=grandeza_industrial_perf.objects.get(
                            id=item.industrial.id
                        )
                    )[0]
                )  # melhorar nao robusto se nao tiver valort na lista
            # print("visRel", variaveis_industriais_sel)

            saida = {}
            saida["variaveis_industriais"] = serializers.serialize(
                "json", variaveis_industriais_sel
            )
            saida["saida"] = True
        except:
            saida = {}
            saida["variaveis_industriais"] = ""
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")
      
def resolve_rig(poco, inicio, fim):
  url = os.getenv("SONDA_POCO_URL")
  pwd = os.getenv("SONDA_POCO_PWD")
  
  basic = HTTPBasicAuth('APP_GIDEAO', pwd)
  ret = requests.get(url + "/" + poco + "/" + inicio + "/" + fim, auth=basic, verify=False)
  
  return ret.text.lower().replace("-", "")

@login_required()      
def ajax_coletar_dados_variaveis_entrada_perf(request):
    # print("EM coleta dados var input", request.POST, "8888")
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        poco_sel = poco_perf.objects.get(id=int(request.POST["poco"]))
        ge_sel = grandeza_especialista_perf.objects.get(
            id=int(request.POST["grandeza_especialista"])
        )
        grandezas_industriais_rel = relacao_especialista_industrial_perf.objects.filter(
            especialista=ge_sel
        )
        variaveis_industriais_sel = []
        unidades_medida_sel = {}
        vis_ids = []
        # print('aqui2', grandezas_industriais_rel)

        for item in grandezas_industriais_rel:
            # print('* ------> ',item)
            item_lista = variavel_industrial_perf.objects.filter(poco=poco_sel).filter(
                grandeza_industrial=grandeza_industrial_perf.objects.get(
                    id=item.industrial.id
                )
            )
            # print('aqui 2,5', type(item_lista), '--')
            if item_lista:
                # print('2,75')
                variaveis_industriais_sel.append(
                    item_lista
                )  # melhorar nao robusto se nao tiver valort na lista
                vis_ids.append(item_lista[0].id)
        variaveis_industriais_sel = variavel_industrial_perf.objects.filter(
            pk__in=vis_ids
        ).order_by("nome")
        
        fim = request.POST["fim"]
        inicio = request.POST["inicio"]
        
        # resolver sonda
        cache_sonda = {}
        
        # print('----------- > aqui 3')
        # Aquisitando dados do PI
        vsn_v = []
        vsn_t = []
        unidade_valores = []
        DadosTrendIndividuais = []
        Status = []
        flag = False  # se algum der sucesso entao eh True
        t_aux = []
        um_aux = None
        sonda = None
        servidor = None
        # print('vis -->', variaveis_industriais_sel)
        for variavelL in list(variaveis_industriais_sel):
            variavel = variavelL
            DadosTrend = "date"
            # DadosTrend=DadosTrend+',' + grandeza_industrial.objects.get(nome=variavel.grandeza_industrial).values_list('nome',flat=True)+'\n'
            DadosTrend = DadosTrend + "," + variavel.grandeza_industrial.nome + "\n"
            # estadosDiscretos = str(variavel.um.unidade_medida_padrao) == "discreta"
            estadosDiscretos = True
            
            try:
                # teste de chamada do servidor PI dedicado
                sonda = cache_sonda.get(variavel.poco.nome, None)
                if sonda is None:
                  sonda = resolve_rig(variavel.poco.nome, inicio, fim)
                  cache_sonda[variavel.poco.nome] = sonda          
                
                rto_data = get_rto_data(variavel.grandeza_industrial.nome, sonda, inicio, fim)                
                received = rto_data["data"]
                servidor = rto_data["server"]
                                
                t_aux = []
                v_aux = []
                um_aux = None
                for item in received:
                  t_aux.append(item["timestamp"])
                  v_aux.append(item["value"])                  
                  um_aux = item["unit"]
                  
                if len(v_aux) == 0 or (v_aux[0] == "" and all(x == v_aux[0] for x in v_aux)):
                    Status.append("NoData")
                else:
                    Status.append("Sucesso")
                flag = True
            except Exception as error:
                v_aux = []
                Status.append("Erro")
            vsn_v.append(v_aux)
            vsn_t.append(t_aux)
            unidade_valores.append(um_aux)
            
        # print('flag', flag)
        saida2 = {}
        # variaveis_industriais_sel = variavel_industrial.objects.filter(pk__in=vis_ids)
        saida2["variaveis"] = serializers.serialize("json", variaveis_industriais_sel)
        saida2["unidades_medida_sel"] = unidades_medida_sel
        saida2["unidade_valores"] = unidade_valores
        saida2["valores"] = vsn_v
        saida2["tempos"] = vsn_t
        saida2["status"] = Status
        saida2["sonda"] = sonda
        saida2["servidor"] = servidor        
        
        return HttpResponse(json.dumps(saida2), content_type="application/json")

@login_required()    
@transaction.atomic  
def ajax_adicionar_instancia_amostras_especialista_perf(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        if request.POST:
            if len(request.POST["inicio"]) == 16:
                analise_inicio_str = request.POST["inicio"] + ":00"
            else:
                analise_inicio_str = request.POST["inicio"]
            if len(request.POST["fim"]) == 16:
                analise_fim_str = request.POST["fim"] + ":00"
            else:
                analise_fim_str = request.POST["fim"]
            # print("antes do try")
            try:
                sonda = None
                for row in sonda_perf.objects.raw("select * from monitor_app_sonda_perf"):
                  if row.nome.lower().replace("-", "") == request.POST["sonda"]:
                    sonda = row
                    break
                  
                # adiciona a analise: ge, poco, usuario, exportacao_habilitada, data_registro
                new_analise = analise_perf(
                    grandeza_especialista=grandeza_especialista_perf.objects.get(
                        id=int(request.POST["grandeza_especialista"])
                    ),
                    poco=poco_perf.objects.get(id=int(request.POST["poco"])),
                    usuario=request.user,
                    exportacao_habilitada=True,
                    data_registro=datetime.datetime.now(),
                    data_inicio=datetime.datetime.strptime(
                        analise_inicio_str, "%Y-%m-%dT%H:%M:%S"
                    ),
                    data_fim=datetime.datetime.strptime(
                        analise_fim_str, "%Y-%m-%dT%H:%M:%S"
                    ),
                    servidor=servidor_perf.objects.get(nome = request.POST["servidor"]),
                    sonda=sonda
                )
                # print("antes de salvar analise")
                # print(request.POST)
                new_analise.save()
                # print("apos salvar analise")
                ge_sel = grandeza_especialista_perf.objects.get(
                    id=int(request.POST["grandeza_especialista"])
                )
                inicios = request.POST.getlist("inicios[]")
                fins = request.POST.getlist("fins[]")
                rotulos = request.POST.getlist("rotulos[]")
                rotulo_sel = ""
                for index in range(0, len(rotulos)):
                    rotulo_sel = str(rotulos[index])
                    new_amostra = []
                    new_amostra = amostra_perf(
                        analise_id=new_analise.id,
                        inicio=datetime.datetime.strptime(
                            inicios[index], "%Y-%m-%dT%H:%M:%S"
                        ),
                        fim=datetime.datetime.strptime(
                            fins[index], "%Y-%m-%dT%H:%M:%S"
                        ),
                        tipo=rotulo_sel
                    )
                    # print("antes de salvar amostra")
                    new_amostra.save()
                    # print("apos salvar amostra")
                # adiciona as amostras: gi, analise, inicio, fim, tipo
                status = True
            except Exception as error:
                status = False
        else:
            status = False
        saida2 = {}
        saida2["status"] = status
        return HttpResponse(json.dumps(saida2), content_type="application/json")

@login_required()      
@transaction.atomic  
def ajax_editar_instancia_amostras_especialista_perf(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        if request.POST:
            if len(request.POST["inicio"]) == 16:
                analise_inicio_str = request.POST["inicio"] + ":00"
            else:
                analise_inicio_str = request.POST["inicio"]
            if len(request.POST["fim"]) == 16:
                analise_fim_str = request.POST["fim"] + ":00"
            else:
                analise_fim_str = request.POST["fim"]
            try:
                analise_sel = request.POST.getlist("analise_sel[]")
                # print("analise_sel", analise_sel)
                # edita a analise: ge, poco, usuario, exportacao_habilitada, data_registro
                # 1- aquisita analise selecionada se ela estiver nao estiver Atualizando
                lista_analises = analise_perf.objects.filter(id=int(analise_sel[0]))
                # print("aqui")
                if len(lista_analises) == 1:
                    asel = lista_analises[0]
                    # print("modelos analise sel:", asel)
                    # 2- aquisita lista de amostras
                    lista_amostra = amostra_perf.objects.filter(analise=asel)
                    for i_amostra in lista_amostra:
                        # print("deletando amostras antigas")
                        i_amostra.delete()
                    asel.data_inicio = datetime.datetime.strptime(
                        analise_inicio_str, "%Y-%m-%dT%H:%M:%S"
                    )
                    asel.data_fim = datetime.datetime.strptime(
                        analise_fim_str, "%Y-%m-%dT%H:%M:%S"
                    )
                    asel.exportacao_habilitada = True
                    asel.status_exportacao = "Pendente"
                    # print("Analise atualizada: ", asel, asel.status_exportacao)
                    asel.save()
                    # print("salvou o modelo")
                  
                    inicios = request.POST.getlist("inicios[]")
                    fins = request.POST.getlist("fins[]")
                    rotulos = request.POST.getlist("rotulos[]")
                    rotulo_sel = ""
                    for index in range(0, len(rotulos)):
                        rotulo_sel = str(rotulos[index])
                        new_amostra = []
                        new_amostra = amostra_perf(
                            analise_id=asel.id,
                            inicio=datetime.datetime.strptime(
                                inicios[index], "%Y-%m-%dT%H:%M:%S"
                            ),
                            fim=datetime.datetime.strptime(
                                fins[index], "%Y-%m-%dT%H:%M:%S"
                            ),
                            tipo=rotulo_sel
                        )
                        new_amostra.save()

                    # 3- atualiza datas de inicio e fim da analise, status_exportacao Pendente
                else:
                    # print("Nao vai poder fazer o agendamento")
                    status = False
                ##                new_analise = analise(grandeza_especialista=grandeza_especialista.objects.get(id=int(request.POST['grandeza_especialista'])),
                ##                poco=poco.objects.get(id=int(request.POST['poco'])), usuario=request.user,exportacao_habilitada=False,
                ##                data_registro=datetime.datetime.now(), data_inicio=datetime.datetime.strptime(analise_inicio_str, "%Y-%m-%dT%H:%M:%S" ),
                ##                data_fim=datetime.datetime.strptime(analise_fim_str, "%Y-%m-%dT%H:%M:%S" ))

                # adiciona as amostras: gi, analise, inicio, fim, tipo
                status = True
            except Exception as error:
                status = False
        else:
            status = False
        saida2 = {}
        saida2["status"] = status
        return HttpResponse(json.dumps(saida2), content_type="application/json")