from django.urls import path
from . import views

urlpatterns = [
    path("rotulagem/", views.rotulagem, name="Rotulagem"),
    path("exportacao/", views.exportacao, name="Exportação"),
    path("ajax/selecionar_ge_amostra_especialista", views.ajax_selecionar_ge_amostra_especialista),
    path("ajax/obter_dados_variaveis_entrada", views.ajax_coletar_dados_variaveis_entrada),
    path("ajax/adicionar_instancia_amostras_especialista", views.ajax_adicionar_instancia_amostras_especialista),
    path("ajax/editar_instancia_amostras_especialista", views.ajax_editar_instancia_amostras_especialista),
    path("ajax/carregar_instancias_por_ge", views.ajax_carregar_instancia_por_ge),
    path("ajax/carregar_instancias", views.ajax_carregar_instancias),
    path("ajax/carregar_amostras_por_analise", views.ajax_carregar_amostras_por_instancia),
    path("ajax/excluir_instancia_por_id", views.ajax_excluir_instancia_por_id),
    path("ajax/ativar_instancia", views.ajax_ativar_instancia),
    path("ajax/desativar_intancia", views.ajax_desativar_instancia),
       
    path("rotulagem_perf", views.rotulagem_perf, name="Rotulagem Perf"),
    path("rotulagem_perf/<uo>", views.rotulagem_perf, name="Rotulagem Perf"),
    path("rotulagem_perf/<uo>/<ativo>", views.rotulagem_perf, name="Rotulagem Perf"),
    path("rotulagem_perf/<uo>/<ativo>/<poco>", views.rotulagem_perf, name="Rotulagem Perf"),    
    path("rotulagem_perf/<uo>/<ativo>/<poco>/<inicio>", views.rotulagem_perf, name="Rotulagem Perf"),    
    path("rotulagem_perf/<uo>/<ativo>/<poco>/<inicio>/<fim>", views.rotulagem_perf, name="Rotulagem Perf"),    
    
    path("ajax/perf/pocos", views.pocos_perf),    
    path("ajax/perf/selecionar_ge_amostra_especialista", views.ajax_selecionar_ge_amostra_especialista_perf),    
    path("ajax/perf/obter_dados_variaveis_entrada", views.ajax_coletar_dados_variaveis_entrada_perf),
    path("ajax/perf/adicionar_instancia_amostras_especialista", views.ajax_adicionar_instancia_amostras_especialista_perf),
    path("ajax/perf/editar_instancia_amostras_especialista", views.ajax_editar_instancia_amostras_especialista_perf),    
    path("ajax/perf/carregar_instancias_por_ge", views.ajax_carregar_instancia_por_ge_perf),
    path("ajax/perf/carregar_instancias", views.ajax_carregar_instancias_perf),
    path("ajax/perf/carregar_amostras_por_analise", views.ajax_carregar_amostras_por_instancia_perf),
    path("ajax/perf/excluir_instancia_por_id", views.ajax_excluir_instancia_por_id_perf)    
]
