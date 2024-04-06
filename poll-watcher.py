import os
import json
import requests
import logging
import time

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

QUOTES_URL='https://data.alpaca.markets/v2/stocks/quotes/latest'

def quote_json(symbol, quote):
    return json.dumps({'symbol': symbol, 'quote': quote, 'retrieved': str(time.time())})

def env_or_default(env_var, value):
    return value if not env_var in os.environ else os.environ[env_var]

interval = float(env_or_default('ALPACA_POLL_SECONDS', '300'))
bootstrap = env_or_default('KAFKA_BOOTSTRAP', 'dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092')
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

from kafka import KafkaProducer
# producer = KafkaProducer(bootstrap_servers=bootstrap)

with requests.sessions.Session() as session:
    while True:
        response = session.send(prepped)
        if (response.status_code == requests.codes.ok):
            quotes = response.json()['quotes']
            for symbol in quotes.keys():
                # producer.send(
                #     'stock-quotes', 
                #     key=bytearray(symbol, 'utf-8'), 
                #     value=bytearray(quote_json(symbol, quotes[symbol]), 'utf-8')
                # )
                # producer.flush()
                logging.info(quote_json(symbol, quotes[symbol]))
        else:
            logging.error('Error retrieving quotes: ' + response.text)
        time.sleep(interval)
