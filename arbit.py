import requests, ConfigParser, base64, hmac, hashlib, json, pyodbc
# json, uuid, time

#Keys
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('keys.cfg')

kraken_k = config.get("API", "kraken_k")
kraken_pk = config.get("API", "kraken_pk")

gemini_k = config.get("API", "gemini_k")
gemini_pk = config.get("API", "gemini_pk")
gemini_endpoint = config.get("API", "gemini_endpoint")
gemini_test_k = config.get("API", "gemini_test_k")
gemini_test_pk = config.get("API", "gemini_test_pk")
gemini_test_endpoint = config.get("API", "gemini_test_endpoint")

polo_k = config.get("API", "polo_k")
polo_pk = config.get("API", "polo_pk")

connstring = "Driver={ODBC Driver 13 for SQL Server};Server=tcp:"+config.get("DB","server")+";DATABASE="+config.get("DB","database")+";UID="+config.get("DB","uname")+";PWD="+ config.get("DB","pwd")

conn = pyodbc.connect(connstring)
c = conn.cursor()

sandbox = 1
#May need to store max nonce in DB by API, increment from historical max value
nonce = 1

if sandbox == 1:
	gemini_endpoint = gemini_test_endpoint
	gemini_k = gemini_test_k
	gemini_pk = gemini_test_pk

def getnonce(func, endpoint, nonce=None):
	if func == 'get':
		c.execute('select current_nonce from dbo.api_lu where endpoint = (?)',(gemini_endpoint,))
		row = c.fetchone()
		return row[0]
	elif func == 'update' and nonce != None:
		c.execute('update dbo.api_lu set current_nonce = (?) where endpoint = (?)',(nonce,gemini_endpoint))
		conn.commit()
		return 1
	else: 
		raise 

def show_response(r):
	if r.raise_for_status():
		r.raise_for_status()
	else:
		print(r.status_code)
		print (r.headers)
		print json.dumps(r.json(), indent=4)
		print('Success!')

def gemini_private(func, pair=None, amt=None, price=None):
	#https://docs.gemini.com/rest-api/#private-api-invocation

	nonce = getnonce(func='get', endpoint=gemini_endpoint)

	if func == 'cancelall':
		request = "/v1/order/cancel/session"
		url = gemini_endpoint+request
		payload = """{{
					"request": "{r}",
					"nonce": "{n}"
					}}""".format(r=request,n=nonce)
	elif func == 'buy':
		request = "/v1/order/new"
		url = gemini_endpoint+request
		print url
		payload = """{{
			"request": "{r}",
			"nonce": "{n}",

			"symbol": "{p}",
			"amount": "{a}",
			"price": "{pr}",
			"side":"buy",
			"type": "exchange limit"
			}}""".format(r=request,n=nonce,p=pair,a=amt,pr=price)
			#"client_order_id": "20150102-4738721", // A client-specified order token
			#"options": ["maker-or-cancel"] // execution options; may be omitted for a standard limit order
		print payload
	else: 
		return None

	b64 = base64.b64encode(payload)
	sig = hmac.new(gemini_pk, b64, hashlib.sha384).hexdigest()

	headers = {'Content-Type': 'text/plain',
	'Content-Length': '0',
	'X-GEMINI-APIKEY': gemini_k,
	'X-GEMINI-PAYLOAD': b64,
	'X-GEMINI-SIGNATURE': sig}

	r = requests.post(url, headers=headers)
	show_response(r)
	getnonce(func='update', endpoint=gemini_endpoint, nonce=nonce+1)

def gemini_public(pair):
	r =requests.get(gemini_endpoint+"/v1/pubticker/{}".format(pair))
	show_response(r)

#gemini_public('ethusd')
#gemini_private(nonce,func='cancelall')
gemini_private(func='buy',pair='ethusd',amt=1,price=150.00)


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

#429 = Too many requests
