from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import os
import json
import urllib.parse
from datetime import datetime
from dateutil import tz

load_dotenv()

base = os.getenv("PI_URL")
user = os.getenv("PI_USER")
pwd = os.getenv("PI_PWD")

print(base)
print(user)
print(pwd)

startTime = urllib.parse.quote_plus("2025-01-01 15:32:02")
endTime = urllib.parse.quote_plus("2025-01-02 00:00:00")

webId = "F1AbEqQ26vK6-9kO204uuSFAG0gL1dTMqeR7RGRkFAvm4gbbw9tcWBgA4f1MBQxv3T0lHAQU0VTQVVBRjAxXFVPLUVTXFVPLUVTXENBTVBPIEpVQkFSVEVcUE_Dh09TIFBST0RVVE9SRVNcOC1KVUItNTlELUVTU3xBTk0uU1RBVFVTIERBIE0x"
recorded = "https://sesauweb02.petrobras.biz/piwebapi/streams/" + webId + "/recorded?startTime=" + startTime + "&endTime=" + endTime
interpolated = "https://sesauweb02.petrobras.biz/piwebapi/streams/" + webId + "/interpolated?startTime=" + startTime + "&endTime=" + endTime

path = r"\\SESAUAF01\UO-ES\UO-ES\Campo Jubarte\Poços Produtores\8-JUB-59D-ESS|ANM.Status da M1"

path = r"\\SBCPI01\P61-301-PI-6112"

body = {
  "1": {
    "Method": "GET",
    "Resource": base +"/attributes?path=" + path
  },
  "2": {
    "Method": "GET",
    "Resource": "{0}?startTime=2018-03-11T08:52&endTime=2018-03-11T08:59",
    "Parameters": [
      "$.1.Content.Links.RecordedData"
    ],
    "ParentIds": [
      "1"
    ]
  }
}

import truststore
truststore.inject_into_ssl()

basic = HTTPBasicAuth(user, pwd)
resp = requests.post(base + "/batch", json=body, auth=basic)
data = resp.json()
print(data)

# print(recorded)
  
basic = HTTPBasicAuth(user, pwd)
# ret = requests.get(base +"/attributes?path=" + path, auth=basic, verify=False)
# ret = requests.get(recorded, auth=basic, cert='pb.pem')

# json_str = json.dumps(ret.json(), indent=4)

# print(json_str)



def utc_str_to_local(utc_str):
  from_zone = tz.tzutc()
  to_zone = tz.tzlocal()
  utc = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ')
  utc = utc.replace(tzinfo=from_zone)
  return utc.astimezone(to_zone).strftime('%Y-%m-%d %H:%M:%S')


print(utc_str_to_local('2017-07-31T21:00:00Z'))

import certifi
print(certifi.where())