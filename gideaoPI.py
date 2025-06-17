# -*- coding: utf-8 -*-
# Módulo que facilita aquisiçao de dados de servidores PI ou AF

import win32com.client
import os
import sys
import json
import time
import datetime
import pythoncom
import clr
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv()

path_PI = os.getenv("PATH_PI_AF", "C:\\Program Files (x86)\\PIPC\\AF\\PublicAssemblies\\4.0")
AF_SDK = "OSIsoft.AFSDK"
sys.path.append(path_PI)
clr.AddReference(AF_SDK)

from OSIsoft.AF import *
from OSIsoft.AF.PI import *
from OSIsoft.AF.Asset import *
from OSIsoft.AF.Data import *
from OSIsoft.AF.Time import *
from OSIsoft.AF.UnitsOfMeasure import *

attrUM = PICommonPointAttributes.EngineeringUnits
conexoes_pi = []
conexoes_af = []

# Regras gerais para conversões de estados
REGRA_GERAL_ESTADOS_ABERTOS = {
    "aberta",
    "aberto",
    "falha (aberta)",
    "on",
    "open",
    "override aberta",
    "true",
}
REGRA_GERAL_ESTADOS_SEMIABERTOS = {
    "closing",
    "transição (75% fechado)",
    "transição fecha",
    "opening",
    "transição (75% aberto)",
    "transição abre",
    "transição",
}
REGRA_GERAL_ESTADOS_FECHADOS = {
    "closed",
    "falha (fechada)",
    "false",
    "fechada",
    "fechado",
    "off",
    "override fechada",
}

# Regras específicas para conversões do estado específico "normal" utilizado nos
# digitalsets NO_FE e NO_AB exclusivamente na UN-ES
# Se o nome da tag tiver a substring ZSL, ela usa o digitalset NO_FE:
#   fechado -> 0
#   normal -> 1.0 (semiaberto ou aberto, mas escolhemos indicar aberto)
# Se o nome da tag tiver a substring ZSH ou a substring ZAH, ela usa o digitalset NO_AB:
#   aberto -> 1.0
#   normal -> 0 (semiaberto ou fechado, mas escolhemos indicar fechado)
REGRA_UN_ES_NO_FE_ESTADOS_ABERTOS = {"normal"}
REGRA_UN_ES_NO_FE_ESTADOS_SEMIABERTOS = {}
REGRA_UN_ES_NO_FE_ESTADOS_FECHADOS = {"fechado"}
REGRA_UN_ES_NO_AB_ESTADOS_ABERTOS = {"aberto"}
REGRA_UN_ES_NO_AB_ESTADOS_SEMIABERTOS = {}
REGRA_UN_ES_NO_AB_ESTADOS_FECHADOS = {"normal"}

# Estados em dois dicionários para simplificar consultas
ESTADOS_ABERTOS = {
    "GERAL": REGRA_GERAL_ESTADOS_ABERTOS,
    "UN_ES_NO_FE": REGRA_UN_ES_NO_FE_ESTADOS_ABERTOS,
    "UN_ES_NO_AB": REGRA_UN_ES_NO_AB_ESTADOS_ABERTOS,
}
ESTADOS_SEMIABERTOS = {
    "GERAL": REGRA_GERAL_ESTADOS_SEMIABERTOS,
    "UN_ES_NO_FE": REGRA_UN_ES_NO_FE_ESTADOS_SEMIABERTOS,
    "UN_ES_NO_AB": REGRA_UN_ES_NO_AB_ESTADOS_SEMIABERTOS,
}
ESTADOS_FECHADOS = {
    "GERAL": REGRA_GERAL_ESTADOS_FECHADOS,
    "UN_ES_NO_FE": REGRA_UN_ES_NO_FE_ESTADOS_FECHADOS,
    "UN_ES_NO_AB": REGRA_UN_ES_NO_AB_ESTADOS_FECHADOS,
}


def getServidor(nome, tipo="PI"):
    r"""
    Definição
    ----------
    Método para obter objeto de conexão com servidor PI ou AF.

    Parameters
    ----------
    nome : STRING
            NOME DO SERVIDOR
    tipo : STRING, optional
        TIPO DO SERVIDOR PI IY AF. The default is "PI".

    Returns
    -------
    servidor : OSIsoft.AF.PI.PIServer / OSIsoft.AF.PISystem
        OBJETO SERVIDOR.

    Exemplos
    ----------
    Exemplo 1:

        import gideaoPI as gp
        servidorPI = gp.getServidor('SESAUPI01',"PI")
        servidorAF = gp.getServidor('SESAUAF01','AF')
    """
    try:
        global conexoes_pi, conexoes_af
        myPISystem = PISystems()
        if nome:
            if tipo == "PI":
                lista = [a for a in conexoes_pi if a.get_Name().lower() == nome.lower()]
                if lista:
                    servidor = lista[0]
                else:
                    servidor = PIServer.FindPIServer(myPISystem.DefaultPISystem, nome)
                    if servidor:
                        conexoes_pi.append(servidor)
            elif tipo == "AF":
                lista = [a for a in conexoes_af if a.get_Name().lower() == nome.lower()]
                if lista:
                    servidor = lista[0]

                else:
                    servidor = myPISystem[nome]
                    if servidor:
                        conexoes_af.append(servidor)
        else:
            servidor = None
    except:
        servidor = None
    return servidor


def getAFDataBase(nome, piAFLocal):
    r"""
    Definição
    ----------
    Método para aquisitar objeto database do AF.

    Parameters
    ----------
    nome : STRING
        Nome de um database de um servidor AF.
    piAFLocal : OSIsoft.AF.PISystem
        objeto do servidor AF conectado.

    Returns
    -------
    DB : OSIsoft.AF.AFDatabase
        databse do AF.

    Exemplos
    ----------
    Exemplo 1:

        import gideaoPI as gp
        meudb = gp.getAFDataBase("UO-ES", gp.getServidor('SESAUAF01','AF'))
    """
    DB = piAFLocal.Databases.get_Item(nome)
    return DB


def identificaTipo(servidor):
    r"""
    Definição
    ----------
    Método que identificad se o objeto de conexão é um servidor PI ou database AF.

    Parameters
    ----------
    servidor : OSIsoft.AF.PI.PIServer / OSIsoft.AF.AFDatabase
        OBJETO DE CONEXÃO SERVIDOR PI OU DATABASE AF

    Returns
    -------
    tipo : STRING
        'PI' SE OBJETO SERVIDOR PI OU 'AF' DE O SERVIDOR É AF.

    Exemplos
    ----------
    Exemplo 1:

        import gideaoPI as gp
        tipo = gp.idenficaTipo(gp.getServidor('SESAUPI01','PI')
        tipo = gp.identificaTipo(gp.getAFDataBase('UO-ES',gp.getServidor('SESAUAF01',
        tipo='AF')))
    """
    tipo = None
    if servidor.__class__.__name__ == "PIServer":
        tipo = "PI"
    elif servidor.__class__.__name__ == "AFDatabase":
        tipo = "AF"
    return tipo


def pathToAtributoAF(DB, caminho_piAF):
    caminho_piAF = caminho_piAF.replace("\\\\", "")
    caminho_piAF = caminho_piAF.replace("\\", "\\\\")
    lista = caminho_piAF.split("|")
    lista_elementos = lista[0].split("\\\\")
    if len(lista[1].split("\\\\")) > 1:
        elemento_final = lista[1].split("\\\\")[0]
        atributo = lista[1].split("\\\\")[1]
    else:
        atributo = lista[1]
        elemento_final = lista_elementos[-1]
        lista_elementos = lista_elementos[:-1]
    element = DB.Elements.get_Item(lista_elementos[2])
    for el in lista_elementos[3:]:
        element = element.Elements.get_Item(el)
    element = element.Elements.get_Item(elemento_final)
    attribute = element.Attributes.get_Item(atributo)
    return attribute


def identificaRegraCodifEstadosDiscretos(tipo, servidorOUdb, tagOUAttr):
    try:
        nome_servidor = servidorOUdb.get_Name().upper()
        nome_tag = tagOUAttr.upper()
        if tipo == "PI" and nome_servidor == "SESAUPI01":
            if "ZSL" in nome_tag:
                return "UN_ES_NO_FE"
            if "ZSH" in nome_tag or "ZAH" in nome_tag:
                return "UN_ES_NO_AB"
        return "GERAL"        
    except:
        return "GERAL"


def codifiqueEstadoDiscreto(estado, regra):
    r"""
    Definição
    ----------
    Método que retorna o código associado ao estado discreto passado por parâmetro.

    Parameters
    ----------
    estado : STRING
        SAÍDA STRING DO PI OU AF.
    regra : STRING
        NOME DE REGRA VÁLIDA (CHAVE DE ESTADOS_ABERTOS E ESTADOS_FECHADOS)

    Returns
    -------
    STRING (associada ao estado)
        '0', '1' ou ''.
    """
    estado_padronizado = estado.strip().lower()
    if estado_padronizado in ESTADOS_ABERTOS[regra]:
        return "1.0"
    elif estado_padronizado in ESTADOS_SEMIABERTOS[regra]:
        return "0.5"
    elif estado_padronizado in ESTADOS_FECHADOS[regra]:
        return "0"
    else:
        return ""


def getRecordedPI(servidor_pi, tag, inicio, fim, regra, estadosDiscretos=False):
    timerange = AFTimeRange(inicio, fim)
    try:
        pt = PIPoint.FindPIPoint(servidor_pi, tag)
        recorded = pt.RecordedValues(timerange, AFBoundaryType.Inside, "", False)
        if estadosDiscretos:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        codifiqueEstadoDiscreto(str(x.Value), regra),
                    ),
                    recorded,
                )
            )
        else:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        str(x.Value),
                    ),
                    recorded,
                )
            )
        dfValor = pd.DataFrame(data, columns=["timestamp", "valor"])
    except:
        dfValor = None
    return dfValor


def getRecordedAF(DB, caminho_piAF, inicio, fim, regra, estadosDiscretos=False):
    tr = AFTimeRange(inicio, fim)
    try:
        attribute = pathToAtributoAF(DB, caminho_piAF)
        recorded = attribute.Data.RecordedValues(
            tr, AFBoundaryType.Inside, None, "", False, 0
        )
        if estadosDiscretos:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        codifiqueEstadoDiscreto(str(x.Value), regra),
                    ),
                    recorded,
                )
            )
        else:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        str(x.Value),
                    ),
                    recorded,
                )
            )
        dfValor = pd.DataFrame(data, columns=["timestamp", "valor"])
    except:
        dfValor = None
    return dfValor


def getValoresArmazenados(servidorOUdb, tagOUAttr, inicio, fim, estadosDiscretos=False):
    r"""
    Definição
    ----------
    Aquisita valores aramezenados de uma tag PI ou atributo AF num intervalo entre uma
    data de inicio e fim.

    Parameters
    ----------
    servidorOUdb : OSIsoft.AF.PI.PIServer / OSIsoft.AF.AFDatabase
        DESCRIPTION objeto de conexão com um servidor PI ou database AF.
    tagOUAttr : TYPE String
        DESCRIPTION Tag PI de um sensor ou atributo AF.
    inicio : TYPE String
        DESCRIPTION string com  o datetime do inicio do periodo, pode-se usar  sintaxe
        de tempo do PI.
    fim : TYPE String
        DESCRIPTION string com  o datetime do fim do periodo, pode-se usar  sintaxe de
        tempo do PI.
    estadosDiscretos : TYPE Bool
        DESCRIPTION bool que determina se a tag ou PI ou atributo AF contém estados
        discretos. Se sim, eles são convertidos para códidos. Se não, nenhuma conversão
        é realizada.

    Returns
    -------
    TYPE pandas dataframe
        DESCRIPTION dataframe dom o timestamp e valores aquisitados.

    Exemplos
    ----------
    Exemplo 1:

        import gideaoPI as gp
        valor= gp.getValoresArmazenados(gp.getServidor('SESAUPI01','PI'),
        '30100D_M54_SXV_046','*-3h','*')
        valor1 = gp.getValoresArmazenados(gp.getServidor('SESAUPI01','PI'),
        '30100D_M54_SXV_046','*-3h','*')
        valor2 = gp.getValoresArmazenados(gp.getAFDataBase('UO-ES',
        gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO JUBARTE\POÇOS PRODUTORES\7-JUB-45-ESS|
        VAZÃO DE INIBIDOR DE INCRUSTAÇÃO SUBSEA','*-24h','*')
        valor3 = gp.getValoresArmazenados(gp.getAFDataBase('UO-ES',
        gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO RONCADOR\POÇOS PRODUTORES\7-RO-34D-RJS|
        ALINHAMENTO PARA MANIFOLD DE TESTE','*-24h','*')
        valor4 = gp.getValoresArmazenados(gp.getAFDataBase('UO-ES',
        gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO RONCADOR\POÇOS PRODUTORES\7-RO-34D-RJS|
        ALINHAMENTO PARA MANIFOLD DE TESTE','*-24h','*')
    """
    valor = None
    tipo = identificaTipo(servidorOUdb)
    regra = identificaRegraCodifEstadosDiscretos(tipo, servidorOUdb, tagOUAttr)
    if tipo == "PI":
        valor = getRecordedPI(
            servidorOUdb, tagOUAttr, inicio, fim, regra, estadosDiscretos
        )
    elif tipo == "AF":
        valor = getRecordedAF(
            servidorOUdb, tagOUAttr, inicio, fim, regra, estadosDiscretos
        )
    return valor


def getInterpolatedPI(
    servidor_pi, tag, inicio, fim, intervalo, regra, estadosDiscretos=False
):
    timerange = AFTimeRange(inicio, fim)
    span = AFTimeSpan.Parse(intervalo)
    try:
        pt = PIPoint.FindPIPoint(servidor_pi, tag)
        interpolated = pt.InterpolatedValues(timerange, span, "", False)
        if estadosDiscretos:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        codifiqueEstadoDiscreto(str(x.Value), regra),
                    ),
                    interpolated,
                )
            )
        else:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        str(x.Value),
                    ),
                    interpolated,
                )
            )
        dfValor = pd.DataFrame(data, columns=["timestamp", "valor"])
    except:
        dfValor = None
    return dfValor


def getInterpolatedAF(
    DB, caminho_piAF, inicio, fim, intervalo, regra, estadosDiscretos=False
):
    tr = AFTimeRange(inicio, fim)
    span = AFTimeSpan.Parse(intervalo)
    try:
        attribute = pathToAtributoAF(DB, caminho_piAF)
        recorded = attribute.Data.InterpolatedValues(tr, span, None, "", False)
        if estadosDiscretos:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        codifiqueEstadoDiscreto(str(x.Value), regra),
                    ),
                    recorded,
                )
            )
        else:
            data = list(
                map(
                    lambda x: (
                        x.Timestamp.LocalTime.ToString("yyyy-MM-dd HH:mm:ss"),
                        str(x.Value),
                    ),
                    recorded,
                )
            )
        dfValor = pd.DataFrame(data, columns=["timestamp", "valor"])
    except:
        dfValor = None
    return dfValor


def getValoresInterpolados(
    servidorOUdb, tagOUAttr, inicio, fim, intervalo, estadosDiscretos=False
):
    r"""
    Definição
    ----------
    Aquisita valores interpolados de uma tag PI ou atributo AF num intervalo entre uma
    data de inicio e fim e em um intervalo determinado.

    Parameters
    ----------
    servidorOUdb : OSIsoft.AF.PI.PIServer / OSIsoft.AF.AFDatabase
        DESCRIPTION objeto de conexão com um servidor PI ou database AF.
    tagOUAttr : TYPE String
        DESCRIPTION Tag PI de um sensor ou atributo AF.
    inicio : TYPE String
        DESCRIPTION string com  o datetime do inicio do periodo, pode-se usar  sintaxe
        de tempo do PI.
    fim : TYPE String
        DESCRIPTION string com  o datetime do fim do periodo, pode-se usar  sintaxe de
        tempo do PI.
        intervalo : TYPE String
        DESCRIPTION string com o intervalo para aquisição dos dados iterpolados
        ('1m','1h','2s', ...).
    estadosDiscretos : TYPE Bool
        DESCRIPTION bool que determina se a tag ou PI ou atributo AF contém estados
        discretos. Se sim, eles são convertidos para códidos. Se não, nenhuma conversão
        é realizada.

    Returns
    -------
    TYPE pandas dataframe
        DESCRIPTION dataframe com o timestamp e valores aquisitados.

    Exemplos
    ----------
    Exemplo 1:

        import gideaoPI as gp
        vs1 = gp.getValoresInterpolados(gp.getServidor('SESAUPI01','PI'),
        '30100D_M54_SXV_046','*-3h','*','10m')
        vs2 = gp.getValoresInterpolados(gp.getServidor('SESAUPI01','PI'),
        '30100D_M54_SXV_046','*-3h','*','10m')
        vs3 = gp.getValoresInterpolados(gp.getAFDataBase('UO-ES',
        gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO JUBARTE\POÇOS PRODUTORES\7-JUB-45-ESS|
        VAZÃO DE INIBIDOR DE INCRUSTAÇÃO SUBSEA','*-24h','*','60m')
        vs4 = gp.getValoresInterpolados(gp.getAFDataBase('UO-ES'
        gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO RONCADOR\POÇOS PRODUTORES\7-RO-34D-RJS|
        ALINHAMENTO PARA MANIFOLD DE TESTE','*-24h','*','1h')
        vs5 = gp.getValoresInterpolados(gp.getAFDataBase('UO-ES',
        gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO RONCADOR\POÇOS PRODUTORES\7-RO-34D-RJS|
        ALINHAMENTO PARA MANIFOLD DE TESTE','*-24h','*','1h')
    """
    valor = None
    tipo = identificaTipo(servidorOUdb)
    regra = identificaRegraCodifEstadosDiscretos(tipo, servidorOUdb, tagOUAttr)
    if tipo == "PI":
        valor = getInterpolatedPI(
            servidorOUdb, tagOUAttr, inicio, fim, intervalo, regra, estadosDiscretos
        )
    elif tipo == "AF":
        valor = getInterpolatedAF(
            servidorOUdb, tagOUAttr, inicio, fim, intervalo, regra, estadosDiscretos
        )
    return valor


def getUMPI(servidor_pi, tag):
    valor = ""
    try:
        pt = PIPoint.FindPIPoint(servidor_pi, tag)
        # verificar se funciona com None ou sem parametro
        # pt.LoadAttributes(None)
        pt.LoadAttributes()
        um = pt.GetAttribute(attrUM)
        valor = um
    except:
        valor = ""
    return valor


def getUMAF(DB, caminho_piAF):
    valor = ""
    try:
        attribute = pathToAtributoAF(DB, caminho_piAF)
        valor = attribute.DefaultUOM.ToString()
    except:
        valor = None
    return valor


def getUM(servidorOUdb, tagOUAttr):
    r"""
    Definição
    ----------
    Retorna  a unidade de medida de engenharia de uma tag PI ou atributo AF.

    Parameters
    ----------
    servidorOUdb : OSIsoft.AF.PI.PIServer / OSIsoft.AF.AFDatabase
        DESCRIPTION objeto de conexão com um servidor PI ou database AF.
    tagOUAttr : TYPE String
        DESCRIPTION Tag PI de um sensor ou atributo AF.

    Returns
    -------
    valor : TYPE String
        DESCRIPTION Unidade de engenharia do PI ou AF.

    Exemplos
    ----------
    Exemplo 1:

        import gideaoPI as gp
        umPI = gp.getUM(gp.getServidor('SESAUPI01','PI'), '30100D_M54_PI_049')
        umAF = gp.getUM(gp.getAFDataBase('UO-ES',gp.getServidor('SESAUAF01','AF')),
        r'\\SESAUAF01\UO-ES\UO-ES\CAMPO JUBARTE\POÇOS PRODUTORES\7-JUB-45-ESS|
        VAZÃO DE INIBIDOR DE INCRUSTAÇÃO SUBSEA')

    """
    try:
        if servidorOUdb:
            tipo = identificaTipo(servidorOUdb)
            if tipo == "PI":
                valor = getUMPI(servidorOUdb, tagOUAttr)
            elif tipo == "AF":
                valor = getUMAF(servidorOUdb, tagOUAttr)
        else:
            valor = ""
            erro = "Falha na conexão com o servidor especificado."
    except:
        valor = ""
        erro = "Erro global na aquisição da UM."
    return valor
