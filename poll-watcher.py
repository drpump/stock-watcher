import os
import json
import requests
import logging
import time
import kafka_pub

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

QUOTES_URL='https://data.alpaca.markets/v2/stocks/quotes/latest'

def env_or_default(env_var, value):
    return value if not env_var in os.environ else os.environ[env_var]

last_quotes={}
def is_dupe(symbol, quote):
    global last_quotes
    if symbol in last_quotes and quote["t"] == last_quotes[symbol]["t"]:
        logging.debug("Duplicate quote for " + symbol)
        return True
    else:
        last_quotes[symbol] = quote
        return False

interval = float(env_or_default('ALPACA_POLL_SECONDS', '300'))
symbols = env_or_default('STOCK_SYMBOLS', 'RMD,AAPL').split(',')

prepped = requests.Request(
    'GET',
    QUOTES_URL,
    params={'symbols': ','.join(symbols)},
    headers={
        'APCA-API-KEY-ID': os.environ['ALPACA_KEY'], 
        'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET'] 
    }
).prepare()

with requests.sessions.Session() as session:
    while True:
        response = session.send(prepped)
        if (response.status_code == requests.codes.ok):
            quotes = response.json()['quotes']
            for symbol in quotes.keys():
                if not is_dupe(symbol, quotes[symbol]):
                    kafka_pub.send_quote(symbol, quotes[symbol])
            kafka_pub.flush()
        else:
            logging.error('Error retrieving quotes: ' + response.text)
        time.sleep(interval)
