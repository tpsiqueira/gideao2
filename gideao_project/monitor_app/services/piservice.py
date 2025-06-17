from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import os
import pandas as pd
from datetime import datetime
from dateutil import tz
import base64
import truststore

truststore.inject_into_ssl()

load_dotenv()

base = os.getenv("PI_URL")
user = os.getenv("PI_USER")
pwd = os.getenv("PI_PWD")
basic = HTTPBasicAuth(user, pwd)

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

def generate_webid_tag (pi_server, tag):
    path_tag =  '\\\\'+ pi_server + '\\' + tag
    encoded_path = base64.b64encode(path_tag[2:].upper().encode('utf-8')).decode()
    webid_tag = 'P1DP' + encoded_path.strip('=').replace('+', '-').replace('/', '_')
    return webid_tag
  
def generate_webid_attribute (af_path_attribute):    
    encoded_path = base64.b64encode(af_path_attribute[2:].upper().encode('utf-8')).decode()
    webid_attribute = 'P1AbE' + encoded_path.strip('=').replace('+', '-').replace('/', '_')    
    return webid_attribute


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
    
def arrumaTemposValores(dfgp):
  tempos = ",".join(dfgp["timestamp"].tolist())
  valores = ",".join(dfgp["valor"].astype(str).tolist())
  saida = tempos[:-1] + "\n" + valores[:-1]
  return saida
    
def utc_str_to_local(utc_str):
  from_zone = tz.tzutc()
  to_zone = tz.tzlocal()
  utc = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ')
  utc = utc.replace(tzinfo=from_zone)
  return utc.astimezone(to_zone).strftime('%Y-%m-%d %H:%M:%S')

def prepare_pi_data_req(label, variavel, inicio, fim):
  payload = None
  tipo = None
  if variavel.is_af:
    tipo = "AF"
    payload = get_pi_af_payload(label, variavel, inicio, fim)
  elif variavel.servidor_pi != "":
    tipo = "PI"
    payload = get_pi_payload(label, variavel, inicio, fim)
    
  regra = identificaRegraCodifEstadosDiscretos(tipo, variavel.servidor_pi, variavel.tag)
    
  return {"payload": payload, "regra": regra} 
    
def run_batch(batch, meta):
  ret = {}
  resp = requests.post(base + "/batch", json=batch, auth=basic)
  resp_data = resp.json()
  for k in resp_data:
    if resp_data[k]['Status'] == 200:
      regra = meta[k]['regra']
      estados_discretos = meta[k]['estados_discretos']
      ret[k] = resolve_resp(resp_data[k]['Content']['Items'], estados_discretos, regra) 
  return ret  

def resolve_resp(items, estados_discretos, regra):
  try:
    if estados_discretos:
      data = list(
        map(lambda x: (
          utc_str_to_local(x['Timestamp']),
          codifiqueEstadoDiscreto(x['Value']['Name'], regra),
        ), items)
      )
    else:
      data = list(
        map(lambda x: (
          utc_str_to_local(x['Timestamp']),
          str(x['Value']),
        ), items)
    )
    return arrumaTemposValores(pd.DataFrame(data, columns=["timestamp", "valor"]))
  except Exception as error:
    print(error)
    return None

def get_pi_payload(label, variavel, inicio, fim):
  body = {}
  webId = generate_webid_tag(variavel.servidor_pi, variavel.tag)
    
  url = base + '/streams/' + webId + '/' + 'recorded'
  body[label] = {
    "Method": "GET",
    "Resource": url + "?startTime=" + inicio + "&endTime=" + fim    
  }  
  return body

def get_pi_af_payload(label, variavel, inicio, fim):
  body = {}
  webId = generate_webid_attribute(variavel.tag)
  
  url = base + '/streams/' + webId + '/' + 'recorded'
  body[label] = {
    "Method": "GET",
    "Resource": url + "?startTime=" + inicio + "&endTime=" + fim    
  }   
  
  return body