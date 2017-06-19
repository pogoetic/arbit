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

def kraken(func, pair=None, amt=None, price=None):
    #rate limits: Only placing orders you intend to fill and keeping the rate down to 1 per second is generally enough to not hit this limit.
    #headers
    k = krakenex.API()
    k.load_key('keys.cfg')

    if func == 'balance':
        r = k.query_private('Balance')
        print json.dumps(r, indent=4)

    elif func == 'assets': #get list of all Kraken currencies
        payload = {'aclass':'currency'}
        if pair!=None:
            payload['asset']=pair
        r = k.query_public('Assets', payload)    
        print json.dumps(r, indent=4)

    elif func == 'fees':
        payload = {}
        if pair!=None:
            payload['pair']=pair
        r = k.query_public('AssetPairs', payload)    
        #print json.dumps(r, indent=4)
        return r

    elif func == 'quote' and pair!=None: #get list of all Kraken currencies
        payload = {'pair': pair}
        r = k.query_public('Ticker', payload)    
        return r
        
    elif func == 'buy':
        return None
    else: 
        return None
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

def networkfees(asset):
    if asset == 'BTC':
        endpoint='https://bitcoinfees.21.co/api/v1/fees/recommended'
        r =requests.get(endpoint)
        r = r.json()
        print 'BTC Fee: '+str(r['fastestFee']*0.00000001)
        print 'Expected Cost BTC = '+ str(225*r['fastestFee']*0.00000001)
    elif asset == 'ETH':
        endpoint='https://api.blockcypher.com/v1/eth/main'
        r =requests.get(endpoint)
        r = r.json()
        print 'ETH Fee: '+str(r['high_gas_price']*0.000000000000000001)
        print 'Expected cost ETH = '+str(21000*r['high_gas_price']*0.000000000000000001)

#gemini_public('ethusd')
#gemini_private(func='cancelall')
#gemini_private(func='buy',pair='ethusd',amt=1,price=150.00)
#kraken(func='assets')  #optional: pair='XBT' (USDT,XXBT,XETH)
r = kraken(func='fees', pair='XXBTZUSD,XETHZUSD,USDTZUSD')  #optional: pair='XXBTZUSD,XETHZUSD,USDTZUSD'
#print json.dumps(r, indent=4)
print 'XXBTZUSD buy fee: '+str(r['result']['XXBTZUSD']['fees'][0][1])
print 'XXBTZUSD sell fee: '+str(r['result']['XXBTZUSD']['fees_maker'][0][1])
print 'XETHZUSD buy fee: '+str(r['result']['XETHZUSD']['fees'][0][1])
print 'XETHZUSD sell fee: '+str(r['result']['XETHZUSD']['fees_maker'][0][1])
print 'USDTZUSD buy fee: '+str(r['result']['USDTZUSD']['fees'][0][1])
print 'USDTZUSD sell fee: '+str(r['result']['USDTZUSD']['fees_maker'][0][1])

r = kraken(func='quote', pair='XXBTZUSD,XETHZUSD,USDTZUSD')
print 'XXBTZUSD ask: '+str(r['result']['XXBTZUSD']['a'][0])
print 'XXBTZUSD bid: '+str(r['result']['XXBTZUSD']['b'][0])
print 'XETHZUSD ask: '+str(r['result']['XETHZUSD']['a'][0])
print 'XETHZUSD bid: '+str(r['result']['XETHZUSD']['b'][0])
print 'USDTZUSD ask: '+str(r['result']['USDTZUSD']['a'][0])
print 'USDTZUSD bid: '+str(r['result']['USDTZUSD']['b'][0])

networkfees('BTC')
networkfees('ETH')




#Bitcoin xfer Fees
#https://bitcoinfees.21.co/api
    # The lowest fee (in satoshis per byte) that will currently result in the fastest transaction confirmations (usually 0 to 1 block delay).
    #rough estimate of tx bytes = in*180 + out*34 + 10 plus or minus 'in' [https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending]
    #1 in and 1 out roughly = 225 bytes
    #https://bitcoinfees.21.co/api/v1/fees/recommended

#ETH xfer fees
#https://www.blockcypher.com/dev/ethereum/#chain-endpoint
    #Returns the current gas price in Wei (1Wei = 0.000000000000000001 ETH)
    #https://api.blockcypher.com/v1/eth/main