from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="Home"),
    path("ajax_adicionar_unidade_operacional", views.ajax_adicionar_uo),
    path("ajax_editar_unidade_operacional", views.ajax_editar_uo),
    path("ajax_excluir_unidade_operacional", views.ajax_excluir_uo),
    path("ajax_adicionar_ativo", views.ajax_adicionar_ativo),
    path("ajax_editar_ativo", views.ajax_editar_ativo),
    path("ajax_excluir_ativo", views.ajax_excluir_ativo),
    path("ajax_adicionar_uep", views.ajax_adicionar_uep),
    path("ajax_editar_uep", views.ajax_editar_uep),
    path("ajax_excluir_uep", views.ajax_excluir_uep),
    path("ajax_adicionar_poco", views.ajax_adicionar_poco),
    path("ajax_editar_poco", views.ajax_editar_poco),
    path("ajax_excluir_poco", views.ajax_excluir_poco),
    path("ajax_adicionar_variavel_industrial", views.ajax_adicionar_variavel_industrial),
    path("ajax_editar_variavel_industrial", views.ajax_editar_variavel_industrial),
    path("ajax_excluir_variavel_industrial", views.ajax_excluir_variavel_industrial),
]
