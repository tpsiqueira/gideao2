#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import datetime


class uo(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.nome


class uo_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.nome


class ativo(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    uo = models.ForeignKey(uo, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class ativo_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    uo = models.ForeignKey(uo_perf, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class uep(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    ativo = models.ForeignKey(ativo, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class poco(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    uep = models.ForeignKey(uep, null=True, blank=True, on_delete=models.CASCADE)
    is_font_vip_xlsx = models.BooleanField(default=True, null=False, blank=False)
    is_not_font_vip_xlsx_date = models.DateTimeField(null=True, blank=True)
    is_not_font_vip_xlsx_obs = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.nome


class poco_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    ativo = models.ForeignKey(
        ativo_perf, null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return self.nome


class unidade_medida_padrao(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.nome


class unidade_medida(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    unidade_medida_padrao = models.ForeignKey(
        unidade_medida_padrao, on_delete=models.SET_NULL, null=True, blank=True
    )
    coeficiente_angular = models.FloatField(null=True, blank=True)
    coeficiente_linear = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.nome


class grandeza_industrial(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.nome


class grandeza_industrial_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    um = models.CharField(max_length=50, null=True, blank=True)
    localizacao = models.CharField(max_length=50, null=True, blank=True)
    origem = models.CharField(max_length=50, null=True, blank=True)
    descricao = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.nome


class grandeza_especialista(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    rotulo_normalidade = models.IntegerField(default=0, null=True, blank=True)
    rotulo_transient = models.IntegerField(default=0, null=True, blank=True)
    rotulo_steady_state = models.IntegerField(default=0, null=True, blank=True)
    periodo_amostra_inicial_nao_rotulada = models.IntegerField(
        default=0, null=True, blank=True
    )

    def __str__(self):
        return self.nome


class grandeza_especialista_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)
    rotulo_normalidade = models.IntegerField(default=0, null=True, blank=True)
    rotulo_transient = models.IntegerField(default=0, null=True, blank=True)
    rotulo_steady_state = models.IntegerField(default=0, null=True, blank=True)
    periodo_amostra_inicial_nao_rotulada = models.IntegerField(
        default=0, null=True, blank=True
    )

    def __str__(self):
        return self.nome


class variavel_industrial(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=True, blank=True)
    poco = models.ForeignKey(poco, null=True, blank=True, on_delete=models.CASCADE)
    grandeza_industrial = models.ForeignKey(
        grandeza_industrial, null=True, blank=True, on_delete=models.CASCADE
    )
    is_font_vip_api = models.BooleanField(default=True, null=False, blank=False)
    is_not_font_vip_api_date = models.DateTimeField(null=True, blank=True)
    is_not_font_vip_api_obs = models.CharField(max_length=300, null=True, blank=True)
    is_font_pi_system = models.BooleanField(null=True, blank=True)
    is_not_font_pi_system_date = models.DateTimeField(null=True, blank=True)
    is_not_font_pi_system_obs = models.CharField(max_length=300, null=True, blank=True)
    is_af = models.BooleanField(null=True, blank=True)
    servidor_pi = models.CharField(max_length=50, null=True, blank=True)
    tag = models.CharField(max_length=500, null=True, blank=True)
    um = models.ForeignKey(
        unidade_medida, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ("grandeza_industrial", "poco")

    def __str__(self):
        return self.nome


class variavel_industrial_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=True, blank=True)
    poco = models.ForeignKey(poco_perf, null=True, blank=True, on_delete=models.CASCADE)
    grandeza_industrial = models.ForeignKey(
        grandeza_industrial_perf, null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("grandeza_industrial", "poco")

    def __str__(self):
        return self.nome


class relacao_especialista_industrial(models.Model):
    especialista = models.ForeignKey(
        grandeza_especialista, null=True, blank=True, on_delete=models.CASCADE
    )
    industrial = models.ForeignKey(
        grandeza_industrial, null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("especialista", "industrial")

    def __str__(self):
        return str(self.especialista.nome + "/" + self.industrial.nome)


class relacao_especialista_industrial_perf(models.Model):
    especialista = models.ForeignKey(
        grandeza_especialista_perf, null=True, blank=True, on_delete=models.CASCADE
    )
    industrial = models.ForeignKey(
        grandeza_industrial_perf, null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("especialista", "industrial")

    def __str__(self):
        return str(self.especialista.nome + "/" + self.industrial.nome)
