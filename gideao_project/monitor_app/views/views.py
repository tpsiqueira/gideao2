from __future__ import unicode_literals

import json
import os
import sys

import django
from admin_app.models import ativo, poco, uep, uo
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from django.db import transaction

from monitor_app.services.piservice import prepare_pi_data_req, run_batch

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gideao_project.settings")
django.setup()
import datetime
import socket
import sys

from admin_app.models import (
    ativo,
    grandeza_especialista,
    grandeza_industrial,
    poco,
    relacao_especialista_industrial,
    uep,
    uo,
    variavel_industrial,
    unidade_medida,
)
from django.core import serializers
from django.http import HttpResponse
from monitor_app.models import amostra, analise


@login_required()
def rotulagem(request):
    usuario = request.user.username
    usuarios = json.dumps(serializers.serialize("json", User.objects.all()))
    uos = json.dumps(serializers.serialize("json", uo.objects.all().order_by("nome")))
    ativos = json.dumps(
        serializers.serialize("json", ativo.objects.all().order_by("nome"))
    )
    ueps = json.dumps(serializers.serialize("json", uep.objects.all().order_by("nome")))
    pocos = json.dumps(
        serializers.serialize("json", poco.objects.all().order_by("nome"))
    )
    grandezas_industriais = json.dumps(
        serializers.serialize("json", grandeza_industrial.objects.all())
    )
    grandezas_especialistas = json.dumps(
        serializers.serialize(
            "json", grandeza_especialista.objects.all().order_by("nome")
        )
    )
    relacoes = json.dumps(
        serializers.serialize("json", relacao_especialista_industrial.objects.all())
    )
    return render(
        request,
        "monitor/tela_rotulagem.html",
        {
            "usuarios": usuarios,
            "usuario": usuario,
            "uos": uos,
            "ativos": ativos,
            "ueps": ueps,
            "pocos": pocos,
            "grandezas_industriais": grandezas_industriais,
            "grandezas_especialistas": grandezas_especialistas,
            "relacoes": relacoes,
        },
    )

@login_required()    
def ajax_selecionar_ge_amostra_especialista(request): # Seleciona grandezas e variáveis industriais relacionadas a uma grandeza especialista para um poço
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            poco_sel = poco.objects.filter(id=int(request.POST["poco"]))
            ge_sel = grandeza_especialista.objects.filter(
                id=int(request.POST["grandeza_especialista"])
            )

            grandezas_industriais_rel = relacao_especialista_industrial.objects.filter(
                especialista=ge_sel[0]
            )

            variaveis_industriais_sel = []
            for item in grandezas_industriais_rel:
                variaveis_industriais_sel.append(
                    variavel_industrial.objects.filter(poco=poco_sel[0]).filter(
                        grandeza_industrial=grandeza_industrial.objects.get(
                            id=item.industrial.id
                        )
                    )[0]
                )  # melhorar nao robusto se nao tiver valor na lista

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


def converter_numero(vetor): # Converte valores textuais para numéricos
    # print('Em converte NUm: ', vetor)
    saida = []

    def transformar_texto_para_numero(x): # Classifica um valor como positivo, negativo ou desconhecido
        positivo = ["Open", "Aberto", "ABERTO", "Aberta", "ON", "On", "ABERTA"]
        negativo = ["Closed", "Fechado", "FECHADO", "Fechada", "FECHADA", "OFF", "Off"]
        if x in positivo:
            saida = "1"
        elif x in negativo:
            saida = "0"
        else:
            saida = ""
        return saida

    if vetor:
        if vetor[0].replace(".", "", 1).isnumeric():
            # print('é numerico', vetor[0])
            saida = vetor
        else:
            # print('NAO é numerico', vetor[0])
            saida = [transformar_texto_para_numero(i) for i in vetor]
    # print('saida: ', saida)
    return saida

@login_required()
def ajax_coletar_dados_variaveis_entrada(request):
  if os.getenv("PI_API", "SDK") == "WEB":
    return obter_dados_variaveis_entrada_web(request)                
  
  # print("EM coleta dados var input", request.POST, "8888")
  if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
      poco_sel = poco.objects.get(id=int(request.POST["poco"]))
      ge_sel = grandeza_especialista.objects.get(
          id=int(request.POST["grandeza_especialista"])
      )
      grandezas_industriais_rel = relacao_especialista_industrial.objects.filter(
          especialista=ge_sel
      )
      variaveis_industriais_sel = []
      unidades_medida_sel = {}
      vis_ids = []
      # print('aqui2', grandezas_industriais_rel)

      for item in grandezas_industriais_rel:
          # print('* ------> ',item)
          item_lista = variavel_industrial.objects.filter(poco=poco_sel).filter(
              grandeza_industrial=grandeza_industrial.objects.get(
                  id=item.industrial.id
              )
          )
          # print('aqui 2,5', type(item_lista), '--')
          if item_lista:
              # print('2,75')
              variaveis_industriais_sel.append(
                  item_lista
              )  # melhorar nao robusto se nao tiver valort na lista
              um = unidade_medida.objects.get(id=item_lista[0].um.id)
              unidades_medida_sel[um.id] = um.nome
              vis_ids.append(item_lista[0].id)
      variaveis_industriais_sel = variavel_industrial.objects.filter(
          pk__in=vis_ids
      ).order_by("nome")
      fim = request.POST["fim"]
      inicio = request.POST["inicio"]
      # print('----------- > aqui 3')
      # Aquisitando dados do PI
      vsn_v = []
      vsn_t = []
      DadosTrendIndividuais = []
      Status = []
      flag = False  # se algum der sucesso entao eh True
      t_aux = []
      # print('vis -->', variaveis_industriais_sel)
      for variavelL in list(variaveis_industriais_sel):
          variavel = variavelL
          # print('aqui 4')
          # print(variavel, dir(variavel))
          DadosTrend = "date"
          # DadosTrend=DadosTrend+',' + grandeza_industrial.objects.get(nome=variavel.grandeza_industrial).values_list('nome',flat=True)+'\n'
          DadosTrend = DadosTrend + "," + variavel.grandeza_industrial.nome + "\n"
          estadosDiscretos = str(variavel.um.unidade_medida_padrao) == "discreta"
          try:
              # teste de chamada do servidor PI dedicado
              HOST, PORT = os.getenv("PI_DATA_SERVER_HOST", "localhost"), int(os.getenv("PI_DATA_SERVER_PORT", "6969"))
              data = (
                  str(variavel.servidor_pi)
                  + ","
                  + str(variavel.tag)
                  + ","
                  + str(inicio)
                  + ","
                  + str(fim)
                  + ","
                  + str(estadosDiscretos)
              )
              # print('Aqui 5')
              # print('data to pi server, ', data)
              # Cirando socket (SOCK_STREAM --> TCP socket)
              sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              # sock.settimeout(200)
              try:
                  # Conectando com o servidor de dados o PI
                  sock.connect((HOST, PORT))
                  # sock.settimeout(10.0)
                  sock.sendall(str.encode(data))
                  # Recebdno dados do servidor
                  received = sock.recv(10000000)
                  received = received.decode("utf-8")
                  # print('received', received)
                  # print(type(received))
              except socket.timeout:
                  vetor = []
              finally:
                  # sock.settimeout(None)
                  sock.close()
              vetor = received.split("\n")
              t_aux = vetor[0].split(",")  # primeiro string da saida do servico
              v_aux0 = vetor[1].split(",")  # segundo string da saida do servico
              v_aux = converter_numero(v_aux0)
              if len(v_aux) == 0 or (
                  v_aux[0] == "" and all(x == v_aux[0] for x in v_aux)
              ):
                  Status.append("NoData")
              else:
                  Status.append("Sucesso")
              flag = True
          except:
              v_aux = []
              Status.append("Erro")
          vsn_v.append(v_aux)
          vsn_t.append(t_aux)
      # print('flag', flag)
      saida2 = {}
      # variaveis_industriais_sel = variavel_industrial.objects.filter(pk__in=vis_ids)
      saida2["variaveis"] = serializers.serialize("json", variaveis_industriais_sel)
      saida2["unidades_medida_sel"] = unidades_medida_sel
      saida2["valores"] = vsn_v
      saida2["tempos"] = vsn_t
      saida2["status"] = Status
      return HttpResponse(json.dumps(saida2), content_type="application/json")

def obter_dados_variaveis_entrada_web(request):                
    # print("EM coleta dados var input", request.POST, "8888")
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        poco_sel = poco.objects.get(id=int(request.POST["poco"]))
        ge_sel = grandeza_especialista.objects.get(
            id=int(request.POST["grandeza_especialista"])
        )
        grandezas_industriais_rel = relacao_especialista_industrial.objects.filter(
            especialista=ge_sel
        )
        variaveis_industriais_sel = []
        unidades_medida_sel = {}
        vis_ids = []
        # print('aqui2', grandezas_industriais_rel)

        for item in grandezas_industriais_rel:
            # print('* ------> ',item)
            item_lista = variavel_industrial.objects.filter(poco=poco_sel).filter(
                grandeza_industrial=grandeza_industrial.objects.get(
                    id=item.industrial.id
                )
            )
            # print('aqui 2,5', type(item_lista), '--')
            if item_lista:
                # print('2,75')
                variaveis_industriais_sel.append(
                    item_lista
                )  # melhorar nao robusto se nao tiver valort na lista
                um = unidade_medida.objects.get(id=item_lista[0].um.id)
                unidades_medida_sel[um.id] = um.nome
                vis_ids.append(item_lista[0].id)
        variaveis_industriais_sel = variavel_industrial.objects.filter(
            pk__in=vis_ids
        ).order_by("nome")
        fim = request.POST["fim"]
        inicio = request.POST["inicio"]
        # print('----------- > aqui 3')
        # Aquisitando dados do PI
        vsn_v = []
        vsn_t = []
        DadosTrendIndividuais = []
        Status = []
        flag = False  # se algum der sucesso entao eh True
        t_aux = []
        batch_max_size = 30
        batch_size = 0
        
        batch = {} 
        batch_res = {}       
        meta = {}
        for variavelL in list(variaveis_industriais_sel):
          variavel = variavelL
          DadosTrend = "date"
          # DadosTrend=DadosTrend+',' + grandeza_industrial.objects.get(nome=variavel.grandeza_industrial).values_list('nome',flat=True)+'\n'
          DadosTrend = DadosTrend + "," + variavel.grandeza_industrial.nome + "\n"
          prepared = prepare_pi_data_req(variavel.grandeza_industrial.nome, variavel, inicio, fim)
          batch_item = prepared['payload']
          meta[variavel.grandeza_industrial.nome] = {
            "regra": prepared['regra'],
            "estados_discretos": str(variavel.um.unidade_medida_padrao) == "discreta"
          }
          
          if batch_item is not None:
            for k in batch_item:
              batch[k] = batch_item[k]
            batch_size = batch_size + 1
            if batch_size == batch_max_size:
              batch_res_item = run_batch(batch, meta)
              for kr in batch_res_item:
                batch_res[kr] = batch_res_item[kr]
              batch_size = 0
              
            
        if batch_size > 0:
          batch_res_item = run_batch(batch, meta)
          for kr in batch_res_item:
            batch_res[kr] = batch_res_item[kr]
              
                  
        for variavelL in list(variaveis_industriais_sel):
            variavel = variavelL
            DadosTrend = "date"
            DadosTrend = DadosTrend + "," + variavel.grandeza_industrial.nome + "\n"
            try:
                received = batch_res[variavel.grandeza_industrial.nome]              
                vetor = received.split("\n")              
                t_aux = vetor[0].split(",")  # primeiro string da saida do servico
                v_aux0 = vetor[1].split(",")  # segundo string da saida do servico
                v_aux = converter_numero(v_aux0)
                if len(v_aux) == 0 or (
                    v_aux[0] == "" and all(x == v_aux[0] for x in v_aux)
                ):
                    Status.append("NoData")
                else:
                    Status.append("Sucesso")
                flag = True
            except:
                v_aux = []
                Status.append("Erro")
            vsn_v.append(v_aux)
            vsn_t.append(t_aux)
        # print('flag', flag)
        saida2 = {}
        # variaveis_industriais_sel = variavel_industrial.objects.filter(pk__in=vis_ids)
        saida2["variaveis"] = serializers.serialize("json", variaveis_industriais_sel)
        saida2["unidades_medida_sel"] = unidades_medida_sel
        saida2["valores"] = vsn_v
        saida2["tempos"] = vsn_t
        saida2["status"] = Status
        return HttpResponse(json.dumps(saida2), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_adicionar_instancia_amostras_especialista(request): # Adiciona uma nova instância com as respectivas amostras e rótulos
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
                # adiciona a analise: ge, poco, usuario, exportacao_habilitada, data_registro
                new_analise = analise(
                    grandeza_especialista=grandeza_especialista.objects.get(
                        id=int(request.POST["grandeza_especialista"])
                    ),
                    poco=poco.objects.get(id=int(request.POST["poco"])),
                    usuario=request.user,
                    exportacao_habilitada=True,
                    data_registro=datetime.datetime.now(),
                    data_inicio=datetime.datetime.strptime(
                        analise_inicio_str, "%Y-%m-%dT%H:%M:%S"
                    ),
                    data_fim=datetime.datetime.strptime(
                        analise_fim_str, "%Y-%m-%dT%H:%M:%S"
                    ),
                )
                # print("antes de salvar analise")
                # print(request.POST)
                new_analise.save()
                # print("apos salvar analise")
                ge_sel = grandeza_especialista.objects.get(
                    id=int(request.POST["grandeza_especialista"])
                )
                inicios = request.POST.getlist("inicios[]")
                fins = request.POST.getlist("fins[]")
                rotulos = request.POST.getlist("rotulos[]")
                rotulo_sel = ""
                estados_poco = request.POST.getlist("estados_poco[]")
                estado_poco_sel = ""
                for index in range(0, len(rotulos)):
                    rotulo_sel = str(rotulos[index])
                    estado_poco_sel = str(estados_poco[index])
                    new_amostra = []
                    new_amostra = amostra(
                        analise_id=new_analise.id,
                        inicio=datetime.datetime.strptime(
                            inicios[index], "%Y-%m-%dT%H:%M:%S"
                        ),
                        fim=datetime.datetime.strptime(
                            fins[index], "%Y-%m-%dT%H:%M:%S"
                        ),
                        tipo=rotulo_sel,
                        estado_poco=estado_poco_sel,
                    )
                    # print("antes de salvar amostra")
                    new_amostra.save()
                    # print("apos salvar amostra")
                # adiciona as amostras: gi, analise, inicio, fim, tipo
                status = True
            except:
                status = False
        else:
            status = False
        saida2 = {}
        saida2["status"] = status
        return HttpResponse(json.dumps(saida2), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_editar_instancia_amostras_especialista(request): # Edita uma instância existente, atualizando suas amostras e rótulos
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
                lista_analises = analise.objects.filter(id=int(analise_sel[0]))
                # print("aqui")
                if len(lista_analises) == 1:
                    asel = lista_analises[0]
                    # print("modelos analise sel:", asel)
                    # 2- aquisita lista de amostras
                    lista_amostra = amostra.objects.filter(analise=asel)
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

                    ge_sel = grandeza_especialista.objects.get(
                        id=int(request.POST["grandeza_especialista"])
                    )
                    inicios = request.POST.getlist("inicios[]")
                    fins = request.POST.getlist("fins[]")
                    rotulos = request.POST.getlist("rotulos[]")
                    rotulo_sel = ""
                    estados_poco = request.POST.getlist("estados_poco[]")
                    estado_poco_sel = ""
                    for index in range(0, len(rotulos)):
                        rotulo_sel = str(rotulos[index])
                        estado_poco_sel = str(estados_poco[index])
                        new_amostra = []
                        new_amostra = amostra(
                            analise_id=asel.id,
                            inicio=datetime.datetime.strptime(
                                inicios[index], "%Y-%m-%dT%H:%M:%S"
                            ),
                            fim=datetime.datetime.strptime(
                                fins[index], "%Y-%m-%dT%H:%M:%S"
                            ),
                            tipo=rotulo_sel,
                            estado_poco=estado_poco_sel,
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
            except:
                status = False
        else:
            status = False
        saida2 = {}
        saida2["status"] = status
        return HttpResponse(json.dumps(saida2), content_type="application/json")

@login_required()
def ajax_carregar_instancia_por_ge(request): # Carrega todas as instâncias relacionadas a uma grandeza especialista
    # print("aqui tb")
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            lista_analises = analise.objects.filter(
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
def ajax_carregar_instancias(request): # Carrega todas as instâncias
    # print("Em carrega analises")
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            lista_analises = analise.objects.all()
            saida = {}
            saida["analises"] = serializers.serialize("json", lista_analises)
            saida["saida"] = True
        except:
            saida = {}
            saida["analises"] = ""
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
def ajax_carregar_amostras_por_instancia(request): # Carrega todas as amostras relacionadas a uma instância
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            lista_amostras = amostra.objects.filter(
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
def ajax_excluir_instancia_por_id(request): # Exclui uma instância específica com base no ID fornecido
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            pk = request.POST["pk"]
            analise_sel = analise.objects.filter(id=int(pk))[0]
            analise_sel.delete()
            saida = {}
            saida["saida"] = True
        except:
            saida = {}
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_ativar_instancia(request): # Ativa a exportação de uma instância para usuários com permissão devida
    # print("Grupos: ", request.user.groups.filter(name="validador").exists())
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            if request.user.groups.filter(name="validador").exists():
                pk = request.POST["pk"]
                analise_sel = analise.objects.filter(id=int(pk))[0]
                analise_sel.exportacao_habilitada = True
                analise_sel.save()
                saida = {}
                saida["saida"] = True
            else:
                saida = {}
                saida["saida"] = False
        except:
            saida = {}
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
@transaction.atomic
def ajax_desativar_instancia(request): # Desativa a exportação de uma instância para usuários com permissão devida
    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.POST:
        try:
            if request.user.groups.filter(name="validador").exists():
                pk = request.POST["pk"]
                analise_sel = analise.objects.filter(id=int(pk))[0]
                analise_sel.exportacao_habilitada = False
                analise_sel.save()
                saida = {}
                saida["saida"] = True
            else:
                saida = {}
                saida["saida"] = False
        except:
            saida = {}
            saida["saida"] = False
        return HttpResponse(json.dumps(saida), content_type="application/json")

@login_required()
def exportacao(request):
    usuario = request.user.username
    usuarios = json.dumps(serializers.serialize("json", User.objects.all()))
    uos = json.dumps(serializers.serialize("json", uo.objects.all().order_by("nome")))
    ativos = json.dumps(
        serializers.serialize("json", ativo.objects.all().order_by("nome"))
    )
    ueps = json.dumps(serializers.serialize("json", uep.objects.all().order_by("nome")))
    pocos = json.dumps(
        serializers.serialize("json", poco.objects.all().order_by("nome"))
    )
    grandezas_industriais = json.dumps(
        serializers.serialize("json", grandeza_industrial.objects.all())
    )
    grandezas_especialistas = json.dumps(
        serializers.serialize(
            "json", grandeza_especialista.objects.all().order_by("nome")
        )
    )
    relacoes = json.dumps(
        serializers.serialize("json", relacao_especialista_industrial.objects.all())
    )
    analises = json.dumps(serializers.serialize("json", analise.objects.all()))
    return render(
        request,
        "monitor/tela_exportacao.html",
        {
            "usuarios": usuarios,
            "usuario": usuario,
            "uos": uos,
            "ativos": ativos,
            "ueps": ueps,
            "pocos": pocos,
            "grandezas_industriais": grandezas_industriais,
            "grandezas_especialistas": grandezas_especialistas,
            "relacoes": relacoes,
            "analises": analises,
        },
    )