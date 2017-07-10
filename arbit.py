import requests
import ConfigParser
import base64
import hmac
import hashlib
import json
import pyodbc
import time
import urllib
import urllib2
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
polo_private_endpoint = config.get("API", "polo_private_endpoint")
polo_public_endpoint = config.get("API", "polo_public_endpoint")

connstring = "Driver={ODBC Driver 13 for SQL Server};Server=tcp:"+config.get("DB","server")+";DATABASE="+config.get("DB","database")+";UID="+config.get("DB","uname")+";PWD="+ config.get("DB","pwd")

conn = pyodbc.connect(connstring)
c = conn.cursor()

sandbox = 1
globalverbose = False

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

def echo(msg, verbose=False):
    if verbose == True or globalverbose == True:
        print msg

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

def kraken_private(method, req={}):
    apiversion = '0'
    req= {'nonce':int(1000*time.time())}
    urlpath ='/' + apiversion + '/private/' + method
    url = kraken_endpoint+urlpath
    postdata = urllib.urlencode(req)
    message = urlpath + hashlib.sha256(str(req['nonce']) + postdata).digest()
    signature = hmac.new(base64.b64decode(kraken_pk), message, hashlib.sha512)
    headers = {'API-Key': kraken_k,
               'API-Sign': base64.b64encode(signature.digest())}
    r = requests.post(url, data=req, headers=headers)
    return r

def kraken(func, pair=None, amt=None, price=None, asset=None):
    while True:
        apiversion = '0'
        req= {'nonce':int(1000*time.time())}
        
        if func == 'quote' and pair!=None: 
            method = 'Ticker'
            req['pair']=pair
            url = kraken_endpoint+ '/' + apiversion + '/public/' + method
            r = requests.post(url, data=req)

        elif func == 'balance':
            r = kraken_private(method='Balance')

        elif func == 'fees':
            method = 'AssetPairs'
            url = kraken_endpoint+ '/' + apiversion + '/public/' + method
            if pair!=None:
                req['pair']=pair
            r = requests.post(url, data=req)  
            #print json.dumps(r.json(), indent=4)

        elif func == 'withdraw':
            req['asset']=asset
            req['amount']=amt
            req['key']='13YLooDEXuf4UtdqchJJ99j2PPAk77Q4Si'
            r = kraken_private(method='WithdrawInfo',req=req)
            show_response(r)

        elif func == 'assets': #get list of all Kraken currencies
            method = 'Assets'
            req['aclass']='currency'
            if pair!=None:
                req['asset']=pair
            url = kraken_endpoint+ '/' + apiversion + '/public/' + method
            r = requests.post(url, data=req)

        else:    
            return None 

        if not r.raise_for_status():
                return r.json()
                break
        else:
            print r.status_code
            continue
    """kraken_private('AddOrder', {'pair': 'XXBTZEUR',
                                 'type': 'buy',
                                 'ordertype': 'limit',
                                 'price': '1',
                                 'volume': '1',
                                 'close[pair]': 'XXBTZEUR',
                                 'close[type]': 'sell',
                                 'close[ordertype]': 'limit',
                                 'close[price]': '9001',
                                 'close[volume]': '1'})"""

def polo_private(command, req = {}):
    req['command'] = command
    req['nonce'] = int(time.time()*1000)
    post_data = urllib.urlencode(req)
    sign = hmac.new(polo_pk, post_data, hashlib.sha512).hexdigest()
    headers = {
        'Key': polo_k,
        'Sign': sign
    }
    r = requests.post(polo_private_endpoint, data=req, headers=headers)

    if command == 'returnBalances':
        filtered = {k: v for k, v in r.json().iteritems() if v!='0.00000000'}
        return filtered
    else:
        return r

def poloniex(func, pair=None, amt=None, price=None):
    req = {}
    while True:
        if func == 'balance':
            r = polo_private(command='returnBalances')
            if not r.raise_for_status():
                return r
                break
            else:
                continue

        if func == 'quote':
            req['command'] = 'returnTicker'
            r = requests.get(polo_public_endpoint,params=req)

        if func == 'fees':
            r = polo_private(command='returnFeeInfo')

        if not r.raise_for_status():
            return r.json()
            break
        else:
            print r.status_code
            continue

def networkfees(asset, exc=None):
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
    if exc is None:
        if asset == 'BTC':
            endpoint='https://bitcoinfees.21.co/api/v1/fees/recommended'
            r =requests.get(endpoint)
            r = r.json()
            #print 'BTC Fee: '+str(r['fastestFee']/100000000.0) #Fee returned in Satoshis per Byte
            #print 'Expected Cost BTC = '+ str(225*r['fastestFee']/100000000.0)
            return 225*r['fastestFee']/100000000.0
        elif asset == 'ETH':
            endpoint='https://api.blockcypher.com/v1/eth/main'
            r =requests.get(endpoint)
            r = r.json()
            #print 'ETH Fee: '+str(r['high_gas_price']/1000000000000000000.0) #Fee returned in Wei per Byte
            #print 'Expected cost ETH = '+str(21000*r['high_gas_price']/1000000000000000000.0)
            return 21000*r['high_gas_price']/1000000000000000000.0
    else: #Exchanges charge fixed fees, no need to calculate
        if exc=='kraken':
            withdrawalfees = {'BTC':0.001,
                              'ETH':0.005,
                              'USDT':5.000,
                              'USD':5.000}
        elif exc =='poloniex':
            withdrawalfees = {'BTC':0.0001,
                              'ETH':0.005,
                              'USDT':2.000}
        return withdrawalfees[asset]


#############################################################






#gemini_public('ethusd')
#gemini_private(func='cancelall')
#gemini_private(func='buy',pair='ethusd',amt=1,price=150.00)

"""
#kraken(func='assets')  #optional: pair='XBT' (USDT,XXBT,XETH)
r = kraken(func='balance')
print r['result']['KFEE']

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
"""

"""
f = kraken(func='fees', pair='XXBTZUSD,XETHZUSD,USDTZUSD')  #optional: pair='XXBTZUSD,XETHZUSD,USDTZUSD'
q = kraken(func='quote', pair='XXBTZUSD,XETHZUSD,USDTZUSD')
amt = 1.0

#Buy BTC
quoteprice = float(q['result']['XXBTZUSD']['a'][0])
purchasecost = amt*quoteprice
tradecost = purchasecost*(f['result']['XXBTZUSD']['fees'][0][1]/100.0)
xfercost = networkfees('BTC')*quoteprice
netbuyvalue = purchasecost - tradecost - xfercost
netbuyamt = amt - (amt*(f['result']['XXBTZUSD']['fees'][0][1]/100.0)) -  networkfees('BTC')
#pay the quoteprice, receive netbuy value in other exchange

print 'quoteprice: '+str(quoteprice)
print 'purchasecost: '+str(purchasecost)
print 'tradecost: '+str(tradecost)
print 'xfercos: '+str(xfercost)
print 'netbuyvalue: '+str(netbuyvalue)
print 'netbuyamt: '+str(netbuyamt)
"""

"""
print networkfees('BTC')
print networkfees('ETH')
print '\n'
"""

"""
r = poloniex(func='balance')
for k, v in r.iteritems():
    print k+' : '+v 

r = poloniex(func='fees')
print json.dumps(r,indent=4)


r = poloniex(func='quote')
print 'BTCUSDT ask: '+str(r['USDT_BTC']['lowestAsk'])
print 'BTCUSDT bid: '+str(r['USDT_BTC']['highestBid'])
print 'ETHUSDT ask: '+str(r['USDT_ETH']['lowestAsk'])
print 'ETHUSDT bid: '+str(r['USDT_ETH']['highestBid'])
"""

"""
q = poloniex(func='quote')
f = poloniex(func='fees')

#Sell BTC
amt = netbuyamt
quoteprice = float(q['USDT_BTC']['highestBid'])
saleproceeds = amt*quoteprice
tradecost = saleproceeds*float(f['makerFee'])

#this wont be in BTC!!!!!
xfercost = networkfees('BTC')*quoteprice 

netsellvalue = saleproceeds - tradecost - xfercost
gainonsale = (netsellvalue/netbuyvalue)-1.0
netsellamt = amt - (amt*float(f['makerFee'])) - networkfees('BTC')

print 'quoteprice:' +str(quoteprice)
print 'saleproceeds: '+str(saleproceeds)
print 'tradecost: '+str(tradecost)
print 'xfercost: '+str(xfercost)
print 'netsellvalue: '+str(netsellvalue)
print 'netsellamt: '+str(netsellamt)
print 'gainonsale: '+str(gainonsale)
"""
print '\n\n'

def checkStrategy(exc,tt,asset,amt=1.0):
    if exc == 'kraken':
        f = kraken(func='fees', pair='XXBTZUSD,XETHZUSD,USDTZUSD')  #optional: pair='XXBTZUSD,XETHZUSD,USDTZUSD'
        q = kraken(func='quote', pair='XXBTZUSD,XETHZUSD,USDTZUSD')
        if asset == 'BTC':
            pair = 'XXBTZUSD'
        elif asset == 'ETH':
            pair = 'XETHZUSD'
        elif asset == 'USDT':
            pair = 'USDTZUSD'
        else:
            return None

        if tt == 'buy':
            feetype = 'fees'
            quotetype = 'a'
            tradefee = f['result'][pair][feetype][0][1]/100.0
            quoteprice = float(q['result'][pair][quotetype][0])
            costorproceed = amt*quoteprice
            tradecost = costorproceed*tradefee
            networkfee = networkfees(asset,exc)
            xfercost = networkfee*quoteprice
            netvalue = costorproceed - tradecost - xfercost
            netamt = amt - (amt*tradefee) - networkfee
            totalcostpct = (amt/netamt) - 1

        elif tt == 'sell':
            feetype = 'fees_maker'
            quotetype = 'b'
            tradefee = f['result'][pair][feetype][0][1]/100.0
            quoteprice = float(q['result'][pair][quotetype][0])
            costorproceed = amt*quoteprice
            tradecost = costorproceed*tradefee
            netvalue = costorproceed - tradecost

            #If selling on Kraken we need to sell to fiat then buy USDT before xfer back
            tradefeeUSDT = f['result']['USDTZUSD'][feetype][0][1]/100.0
            quotepriceUSDT = float(q['result']['USDTZUSD'][quotetype][0])
            networkfeeUSDT = networkfees('USDT','kraken')
            costorproceed = netvalue/quotepriceUSDT
            tradecost = costorproceed*tradefeeUSDT
            netvalue = costorproceed - tradecost - networkfeeUSDT
            netamt = netvalue/quoteprice
            totalcostpct = (amt/netamt) - 1

        return netvalue, netamt, totalcostpct, quoteprice

    elif exc == 'poloniex':
        f = poloniex(func='fees')
        q = poloniex(func='quote')
        #print json.dumps(q,indent=4)
        if asset == 'BTC':
            pair = 'USDT_BTC'
        elif asset == 'ETH':
            pair = 'USDT_ETH'
        else:
            return None

        if tt == 'buy':
            feetype = 'takerFee'
            quotetype = 'lowestAsk'
        elif tt == 'sell':
            feetype = 'makerFee'
            quotetype = 'highestBid'
        else:
            return None

        tradefee = float(f[feetype])
        networkfee = networkfees(asset,exc)
        quoteprice = float(q[pair][quotetype])
        costorproceed = amt*quoteprice
        tradecost = costorproceed*tradefee
        xfercost = networkfee*quoteprice
        netvalue = costorproceed - tradecost - xfercost
        netamt = amt - (amt*tradefee) -  networkfee
        totalcostpct = (amt/netamt) - 1
        return netvalue, netamt, totalcostpct, quoteprice
    else:
        return None 

#Loop through each buy/sell point and currency pair and call checkStrategy. 
buystrat = [{'exc':'kraken','asset':'BTC','tt':'buy'},
            {'exc':'kraken','asset':'ETH','tt':'buy'},
            {'exc':'poloniex','asset':'BTC','tt':'buy'},
            {'exc':'poloniex','asset':'ETH','tt':'buy'}]
for d in buystrat:
    d['netvalue'], d['netamt'], d['totalcostpct'], d['quoteprice'] = checkStrategy(exc=d['exc'],asset=d['asset'],tt=d['tt'])
    for i in d:
        echo(msg=i+': '+str(d[i]))
    echo(msg='\n')

sellstrat = [{'exc':'kraken','asset':'BTC','tt':'sell'},
             {'exc':'kraken','asset':'ETH','tt':'sell'},
             {'exc':'poloniex','asset':'BTC','tt':'sell'},
             {'exc':'poloniex','asset':'ETH','tt':'sell'}]
for d in sellstrat:
    d['netvalue'], d['netamt'], d['totalcostpct'], d['quoteprice'] = checkStrategy(exc=d['exc'],asset=d['asset'],tt=d['tt'])
    for i in d:
        echo(msg=i+': '+str(d[i]))
    echo(msg='\n')

for b in buystrat:
    for s in sellstrat:
        if b['exc'] != s['exc'] and b['asset']==s['asset']:
            #Valid strategies have differing exchange, same asset
            #print b['exc']+'-'+b['asset']+' @'+' -> '+ s['exc']+'-'+s['asset']+' : '+str((s['netvalue']/b['netvalue'])-1.0)+' | totalcostpct : '+str(s['totalcostpct']+b['totalcostpct'])
            print '{}-{} @{} -> {}-{} @{} | netreturn: {} | totalcostpct: {}'.format(b['exc'],b['asset'],b['quoteprice'],s['exc'],s['asset'],s['quoteprice'],str((s['netvalue']/b['netvalue'])-1.0),str(s['totalcostpct']+b['totalcostpct']))


#For Kraken must also factor in additional fees + drift from ZUSD to USDT exchanges
    #If Polo->Kraken there is an extra 'Buy USDT' step before xfer back (this will eat profits)

#checkStrategy = Calculate End-2-End Opportinity (BuySell or SellBuy with ETH/BTC on Kraken/Polo) (8 combinations)
#ExecuteTrade
    #Buy
    #Check that its bought
    #(RECHECK STRATEGY)
    #Transfer
    #Check that its transferred
    #(RECHECK STRATEGY)
    #Sell
    #Check that it sold
    #(RECHECK STRATEGY)
    #Transfer Back, Repeat

#Next: Calculate 'final value of buy+xfer' and 'final value of sell+xfer' for each currency pair
# Compare this value to the same values on the other side and execute if they result in some min gain
# factor in Kraken Fee Credits r = kraken(func='balance') print r['result']['KFEE']

#Use Shapeshift to get money in/out of Gemini or other non USDT exchanges

"""
var unitMap = {
    'wei':          '1',
    'kwei':         '1000',
    'ada':          '1000',
    'femtoether':   '1000',
    'mwei':         '1000000',
    'babbage':      '1000000',
    'picoether':    '1000000',
    'gwei':         '1000000000',
    'shannon':      '1000000000',
    'nanoether':    '1000000000',
    'nano':         '1000000000',
    'szabo':        '1000000000000',
    'microether':   '1000000000000',
    'micro':        '1000000000000',
    'finney':       '1000000000000000',
    'milliether':    '1000000000000000',
    'milli':         '1000000000000000',
    'ether':        '1000000000000000000',
    'kether':       '1000000000000000000000',
    'grand':        '1000000000000000000000',
    'einstein':     '1000000000000000000000',
    'mether':       '1000000000000000000000000',
    'gether':       '1000000000000000000000000000',
    'tether':       '1000000000000000000000000000000'
};
"""