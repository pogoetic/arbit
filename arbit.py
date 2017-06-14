import requests, sqlite3, json, ConfigParser, uuid, time, pyodbc, base64

#Keys
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('keys.cfg')
kraken_k = config.get("API", "kraken_k")
kraken_pk = config.get("API", "kraken_pk")
gemini_k = config.get("API", "gemini_k")
gemini_pk = config.get("API", "gemini_pk")
polo_k = config.get("API", "polo_k")
polo_pk = config.get("API", "polo_pk")
connstring = "Driver={ODBC Driver 13 for SQL Server};Server=tcp:"+config.get("DB","server")+";DATABASE="+config.get("DB","database")+";UID="+config.get("DB","uname")+";PWD="+ config.get("DB","pwd")

#conn = pyodbc.connect(connstring)

#May need to store max nonce in DB by API, increment from historical max value
nonce = 1

#https://docs.gemini.com/rest-api/#private-api-invocation
#Gemini Sandbox https://api.sandbox.gemini.com
#Gemini Live https://api.gemini.com
string = """{
    "request": "/v1/order/status",
    "nonce": {n},

    "order_id": 18834
}
""".format(n=nonce)

print string

b64 = base64.b64encode(string)
nonce+=1

print nonce 

geminikey = hmac.new(gemini_pk, b64, hashlib.sha384).hexdigest()

"""SAMPLE REQUEST

POST /v1/order/status
Content-Type: text/plain
Content-Length: 0
X-GEMINI-APIKEY: mykey
X-GEMINI-PAYLOAD:ewogICAgInJlcXVlc3QiOiAiL3YxL29yZGVyL3N
    0YXR1cyIsCiAgICAibm9uY2UiOiAxMjM0NTYsCgogICAgIm9yZGV
    yX2lkIjogMTg4MzQKfQo=
X-GEMINI-SIGNATURE: 337cc8b4ea692cfe65b4a85fcc9f042b2e3f
    702ac956fd098d600ab15705775017beae402be773ceee10719f
    f70d710f

"""