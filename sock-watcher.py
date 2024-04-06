import websocket
import os
import json
import logging
import time
from kafka import KafkaProducer

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

bootstrap = env_or_default('KAFKA_BOOTSTRAP', 'dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092')
producer = KafkaProducer(bootstrap_servers=bootstrap)

def env_or_default(env_var, value):
    return value if not env_var in os.environ else os.environ[env_var]

def publish_quote(quote):
    quote_json = json.dumps({'symbol': quote["S"], 'quote': quote})
    producer.send(
        'stock-quotes', 
        key=bytearray(symbol, 'utf-8'), 
        value=bytearray(quote_json(symbol, quotes[symbol]), 'utf-8')
    )

def on_message(ws, message):
    msg = json.loads(message)
    for obj in msg:
        match obj["T"]:
            case "subscription":
                logging.info("Subscription confirmed: " + json.dumps(obj))
            case "success":
                logging.info("Success: " + json.dumps(obj))
            case "error":
                logging.error("Error: " + json.dumps(obj))
            case "q":
                logging.info("New quote: " + json.dumps(obj))
            case "t":
                logging.info("New trade: " + json.dumps(obj))
            case _:
                logging.info("Other message: " + json.dumps(obj))

def on_error(ws, error):
    logging.error(f"Error on websocket -- {error}")

def on_close(ws, close_status_code, close_msg):
    logging.warn(f"Websocket closed with status {close_status_code} -- {close_msg}" )

def on_open(ws):
    symbols = env_or_default('STOCK_SYMBOLS', 'RMD,AAPL').split(',')
    subs = json.dumps({
            "action": "subscribe",
            "quotes": symbols
        })
    logging.info("Subscription requested:" + subs)
    ws.send(subs)

# websocket.enableTrace(True)
ws = websocket.WebSocketApp("wss://stream.data.alpaca.markets/v2/iex",
                            header={
                                'APCA-API-KEY-ID': os.environ['ALPACA_KEY'], 
                                'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET'] 
                            },
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.run_forever()