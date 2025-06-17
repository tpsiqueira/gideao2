from .rtomongoservice import *

# -*- coding: utf-8 -*-
# Módulo que facilita aquisiçao de dados do RTOLive

import os
import sys
import json
import time
import datetime
import pythoncom
import clr
import pandas as pd
import re

from pymongo import MongoClient
from dateutil import parser

from dotenv import load_dotenv

load_dotenv()

def get_rto_data(variavel, sonda, inicio, fim):
  ret = {
    "data": [],
    "server": None
  }
  
  strings = os.getenv("RTO_LIVE_DB_STRINGS").split(",")
  # for string in strings:
    # print(string)
    
  # inicio = "2018-03-11T08:52:00"
  # fim = "2018-03-11T08:59:00"
  
  # inicio = "2018-03-11T08:52:00"
  # fim = "2018-03-11T08:59:00"  
    
  inicio_ts = parser.parse(inicio).timestamp()*1000
  fim_ts = parser.parse(fim).timestamp()*1000
  
  print("Obtendo dados da variável " + variavel)
  cont_server = 1
  
  for conn_str in strings:
    client = MongoClient(conn_str)
    with client: 
      # define base de dados 
      db = client.get_database()
      # for item in db.list_collection_names():
        # print(item)
      
      print("Servidor " + str(cont_server))
        
      col_teste = db.events[sonda]
      # item = col_teste.find_one({"adjusted_index_timestamp": {"$gte": inicio_ts, "$lte": fim_ts}}, sort=[('adjusted_index_timestamp', -1)])
      itens = col_teste.find({"mnemonic": variavel, "adjusted_index_timestamp": {"$gte": inicio_ts, "$lte": fim_ts}})
      # itens = col_teste.find({"raw_mnemonic": variavel})
      # ret = col_teste.find()
      
      for item in itens:    
        ret["data"].append({
          "timestamp": datetime.datetime.fromtimestamp(item['adjusted_index_timestamp']/1000).isoformat(), 
          "value": item['value'],
          "unit": item['uom']
        })  
        print(str(item['adjusted_index_timestamp']) + ': ' + item['mnemonic'] + ' ' + item['well_name'] +  ' ' + str(item['value']) + ' ' + item['uom'])
      
      if len(ret["data"]) > 0:
        server_re = re.search(r"mongodb:.+@(.+?)\..+", conn_str, re.IGNORECASE)
        if server_re:
          ret["server"] = server_re.group(1)
        break
    
      cont_server = cont_server + 1
  
  return ret


  # cont = 0
      
      # for item in ret:
      #   if cont == 10:
      #     break
      #   # print(item)
      #   #item['well_name'] => não confiável!!!!!!!!!!
        
      #   print(str(item['adjusted_index_timestamp']) + ': ' + item['raw_mnemonic'] + ' ' + str(item['raw_value']) + ' ' + item['raw_uom'])
      #   print(item['mnemonic'] + ' ' + str(item['value']) + ' ' + item['uom'])
      #   print("--------------------")
        
      #   cont = cont + 1  
      
      