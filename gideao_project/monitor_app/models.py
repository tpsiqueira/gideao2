#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import datetime
from admin_app.models import (
    poco,
    poco_perf,
    grandeza_especialista,
    grandeza_especialista_perf,
)


class sonda_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.nome


class servidor_perf(models.Model):
    nome = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.nome


class lookup_servidor_perf(models.Model):
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    sonda = models.ForeignKey(sonda_perf, on_delete=models.CASCADE)
    servidor = models.ForeignKey(servidor_perf, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("sonda", "servidor")

    def __str__(self):
        return str(self.sonda.nome + "/" + self.servidor.nome)


class analise(models.Model):
    grandeza_especialista = models.ForeignKey(
        grandeza_especialista, on_delete=models.CASCADE
    )
    poco = models.ForeignKey(poco, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_registro = models.DateTimeField(default=timezone.now)
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fim = models.DateTimeField(default=timezone.now)
    exportacao_habilitada = models.BooleanField()
    ChoiceList = (
        ("Pendente", "Pendente"),
        ("Exportando", "Exportando"),
        ("Exportada", "Exportada"),
        ("Erro", "Erro"),
    )
    status_exportacao = models.CharField(
        default="Pendente",
        max_length=15,
        choices=ChoiceList,
        null=True,
        blank=True,
    )

    def __int__(self):
        return self.id


class analise_perf(models.Model):
    grandeza_especialista = models.ForeignKey(
        grandeza_especialista_perf, on_delete=models.CASCADE
    )
    poco = models.ForeignKey(poco_perf, on_delete=models.CASCADE)
    sonda = models.ForeignKey(sonda_perf, on_delete=models.CASCADE)
    servidor = models.ForeignKey(servidor_perf, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_registro = models.DateTimeField(default=timezone.now)
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fim = models.DateTimeField(default=timezone.now)
    exportacao_habilitada = models.BooleanField()
    ChoiceList = (
        ("Pendente", "Pendente"),
        ("Exportando", "Exportando"),
        ("Exportada", "Exportada"),
        ("Erro", "Erro"),
    )
    status_exportacao = models.CharField(
        default="Pendente",
        max_length=15,
        choices=ChoiceList,
        null=True,
        blank=True,
    )

    def __int__(self):
        return self.id


class amostra(models.Model):
    analise = models.ForeignKey(analise, on_delete=models.CASCADE)
    inicio = models.DateTimeField(default=timezone.now)
    fim = models.DateTimeField(default=timezone.now)
    choice_list = (
        ("NORMAL", "NORMAL"),
        ("TRANSIENT", "TRANSIENT"),
        ("STEADY STATE", "STEADY STATE"),
        ("UNKNOWN", "UNKNOWN"),
    )
    tipo = models.CharField(default="NORMAL", max_length=30, choices=choice_list)
    choice_list = (
        ("OPEN", "OPEN"),
        ("SHUT-IN", "SHUT-IN"),
        ("FLUSHING DIESEL", "FLUSHING DIESEL"),
        ("FLUSHING GAS", "FLUSHING GAS"),
        ("BULLHEADING", "BULLHEADING"),
        ("CLOSED WITH DIESEL", "CLOSED WITH DIESEL"),
        ("CLOSED WITH GAS", "CLOSED WITH GAS"),
        ("RESTART", "RESTART"),
        ("DEPRESSURIZATION", "DEPRESSURIZATION"),
        ("UNKNOWN", "UNKNOWN"),
    )
    estado_poco = models.CharField(default="OPEN", max_length=30, choices=choice_list)


class amostra_perf(models.Model):
    analise = models.ForeignKey(analise_perf, on_delete=models.CASCADE)
    inicio = models.DateTimeField(default=timezone.now)
    fim = models.DateTimeField(default=timezone.now)
    choice_list = (
        ("NORMAL", "NORMAL"),
        ("TRANSIENT", "TRANSIENT"),
        ("STEADY STATE", "STEADY STATE"),
        ("UNKNOWN", "UNKNOWN"),
    )
    tipo = models.CharField(default="NORMAL", max_length=30, choices=choice_list)
