import os
import json
import asyncio
import httpx
import logging
import time
import kafka_pub
import prometheus_client
import uvicorn
from fastapi import FastAPI

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

prepped = httpx.Request(
    'GET',
    QUOTES_URL,
    params={'symbols': ','.join(symbols)},
    headers={
        'APCA-API-KEY-ID': os.environ['ALPACA_KEY'], 
        'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET'] 
    }
)

metrics = prometheus_client.make_asgi_app()
app = FastAPI()
app.mount("/metrics", metrics)
config = uvicorn.Config(app=app, port=8002, log_level="info", host="0.0.0.0")
server = uvicorn.Server(config)

async def poll():
    req_counter = prometheus_client.Counter('poll_requests', 'Number of HTTP requests')
    quote_counter = prometheus_client.Counter('poll_quotes', 'Number of unique quotes')
    error_counter = prometheus_client.Counter('poll_errors', 'Number of polling errors')
    async with httpx.AsyncClient(http2=True) as client:
        while True:
            response = await client.send(prepped)
            req_counter.inc()
            if (response.status_code == httpx.codes.ok):
                quotes = response.json()['quotes']
                for symbol in quotes.keys():
                    if not is_dupe(symbol, quotes[symbol]):
                        kafka_pub.send_quote(symbol, quotes[symbol])
                        quote_counter.inc()
                kafka_pub.flush()
            else:
                logging.error('Error retrieving quotes: ' + response.text)
                error_counter.inc()
            await asyncio.sleep(interval)

async def main():
    async with asyncio.TaskGroup() as tg:
        poller = tg.create_task(poll())
        prom = tg.create_task(server.serve())

asyncio.run(main())
