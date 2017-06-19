import requests, ConfigParser, base64, hmac, hashlib, json, pyodbc, time, urllib
import krakenex
# json, uuid

#Keys
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('keys.cfg')

kraken_k = config.get("API", "kraken_k")
kraken_pk = config.get("API", "kraken_pk")
kraken_endpoint = config.get("API", "kraken_endpoint")

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

if sandbox == 1:
    gemini_endpoint = gemini_test_endpoint
    gemini_k = gemini_test_k
    gemini_pk = gemini_test_pk

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

    nonce = int(1000*time.time())

    if func == 'cancelall':
        request = "/v1/order/cancel/session"
        url = gemini_endpoint+request
        payload = """{{
                    "request": "{r}",
                    "nonce": "{n}"
                    }}""".format(r=request,n=str(nonce))
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
            }}""".format(r=request,n=str(nonce),p=pair,a=amt,pr=price)
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

def gemini_public(pair):
    r =requests.get(gemini_endpoint+"/v1/pubticker/{}".format(pair))
    show_response(r)

def kraken_private(func, pair=None, amt=None, price=None):
    #rate limits: Only placing orders you intend to fill and keeping the rate down to 1 per second is generally enough to not hit this limit.
    #headers
    #API-Key = API key
    #API-Sign = Message signature using HMAC-SHA512 of (URI path + SHA256(nonce + POST data)) and base64 decoded secret API key
    nonce = int(1000*time.time())

    if func == 'balance':
        request = "/0/private/Balance"
        url = kraken_endpoint+request
        payload = {"nonce": str(nonce)}
    elif func == 'buy':
        return None
    else: 
        return None

##########
    postdata = urllib.urlencode(payload)
    # Unicode-objects must be encoded before hashing
    #encoded = (str(nonce) + postdata).encode()
    message = request + hashlib.sha256(str(nonce) + postdata).digest()
    signature = hmac.new(base64.b64decode(kraken_pk), message, hashlib.sha512) 
    print base64.b64encode(signature.digest())
#############

    headers = { 'User-Agent': 'Kraken Python API Agent', 
                'API-Key': kraken_k,
                'API-Sign': base64.b64encode(signature.digest())}

    #r = requests.post(url, headers=headers)
    #show_response(r)

#gemini_public('ethusd')
#gemini_private(func='cancelall')
#gemini_private(func='buy',pair='ethusd',amt=1,price=150.00)
#kraken_private(func='balance')  

k = krakenex.API()
k.load_key('keys.cfg')
r = k.query_private('Balance')
print json.dumps(r, indent=4)



"""
k.query_private('AddOrder', {'pair': 'XXBTZEUR',
                             'type': 'buy',
                             'ordertype': 'limit',
                             'price': '1',
                             'volume': '1',
                             'close[pair]': 'XXBTZEUR',
                             'close[type]': 'sell',
                             'close[ordertype]': 'limit',
                             'close[price]': '9001',
                             'close[volume]': '1'})
"""


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
