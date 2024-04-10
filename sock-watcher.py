import websockets
import os
import json
import logging
import time
import kafka_pub
import asyncio
import prometheus_client
import uvicorn
from fastapi import FastAPI

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

SYM_KEY="S"
TYPE_KEY="T"

def env_or_default(env_var, value):
    return value if not env_var in os.environ else os.environ[env_var]

def publish_quote(quote):
    quote_json = json.dumps({'symbol': quote["S"], 'quote': quote})
    producer.send(
        'stock-quotes', 
        key=bytearray(symbol, 'utf-8'), 
        value=bytearray(quote_json(symbol, quotes[symbol]), 'utf-8')
    )

def subs_request(symbols):
    return json.dumps({
            "action": "subscribe",
            "quotes": symbols
    })

def prom_server():
    metrics = prometheus_client.make_asgi_app()
    app = FastAPI()
    app.mount("/metrics", metrics)
    config = uvicorn.Config(app=app, port=8003, log_level="info", host="0.0.0.0")
    return uvicorn.Server(config)


async def sock_watch(symbols):
    quote_counter = prometheus_client.Counter('push_quotes', 'Number of unique quotes')
    error_counter = prometheus_client.Counter('push_errors', 'Number of polling errors')
    headers = {
        'APCA-API-KEY-ID': os.environ['ALPACA_KEY'], 
        'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET'] 
    }
    async with websockets.connect("wss://stream.data.alpaca.markets/v2/iex", extra_headers=headers) as sock:
        async for message in sock:
            parsed = json.loads(message)
            for obj in parsed:
                match obj[TYPE_KEY]:
                    case "subscription":
                        logging.info("Subscription confirmed: " + json.dumps(obj))
                    case "success":
                        logging.info("Success: " + json.dumps(obj))
                        if obj["msg"] == "authenticated":
                            await sock.send(subs_request(symbols))
                    case "error":
                        error_counter.inc()
                        logging.error("Error: " + json.dumps(obj))
                    case "q":
                        quote_counter.inc()
                        kafka_pub.send_quote(obj[SYM_KEY], obj)
                    case "t":
                        logging.info("New trade: " + json.dumps(obj))
                    case _:
                        logging.info("Other message: " + json.dumps(obj))
            kafka_pub.flush()

async def main():
    symbols = env_or_default('STOCK_SYMBOLS', 'RMD,AAPL').split(',')
    async with asyncio.TaskGroup() as tg:
        puller = tg.create_task(sock_watch(symbols))
        prom = tg.create_task(prom_server().serve())

asyncio.run(main())
