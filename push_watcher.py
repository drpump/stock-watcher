import websockets
import json
import logging
import prometheus_client
import kafka_pub
from enum import StrEnum

TYPE_KEY = 'T'
SYM_KEY = 'S'

class TypeCodes(StrEnum): 
    QUOTE = 'q'
    TRADE = 't'
    BAR = 'b'

types = {
    TypeCodes.QUOTE: kafka_pub.QUOTE,
    TypeCodes.TRADE: kafka_pub.TRADE,
    TypeCodes.BAR: kafka_pub.BAR
}
counters = {
    TypeCodes.QUOTE : prometheus_client.Counter('push_quotes', 'Number of unique quotes', ['symbol']),
    TypeCodes.TRADE: prometheus_client.Counter('push_trades', 'Number of unique trades', ['symbol']),
    TypeCodes.BAR: prometheus_client.Counter('push_bars', 'Number of unique bars', ['symbol'])
}
error_counter = prometheus_client.Counter('push_errors', 'Number of polling errors')
 

def env_or_default(env_var, value):
    return value if not env_var in os.environ else os.environ[env_var]

def subs_request(symbols):
    return json.dumps({
            "action": "subscribe",
            "bars": symbols
    })

async def process(message, sock, symbols):
    parsed = json.loads(message)
    for obj in parsed:
        key = obj[TYPE_KEY]
        match key:
            case "subscription":
                logging.info("Subscription confirmed: " + json.dumps(obj))
            case "success":
                logging.info("Success: " + json.dumps(obj))
                if obj["msg"] == "authenticated":
                    await sock.send(subs_request(symbols))
            case TypeCodes.QUOTE | TypeCodes.TRADE | TypeCodes.BAR:
                symbol = obj[SYM_KEY]
                counters[key].labels(symbol).inc()
                await kafka_pub.publish(symbol, types[key], obj)
            case "error":
                error_counter.inc()
                logging.error("Error: " + json.dumps(obj))
            case _:
                logging.warn("Unrecognized message: " + json.dumps(obj))
    await kafka_pub.flush()

async def pusher(symbols, auth):
    async with websockets.connect("wss://stream.data.alpaca.markets/v2/iex", extra_headers=auth) as sock:
        async for message in sock:
            await process(message, sock, symbols)

