import os
import json
import httpx
import logging
import kafka_pub
import prometheus_client
import asyncio

QUOTES_URL='https://data.alpaca.markets/v2/stocks/quotes/latest'
last_quotes={}

def is_dupe(symbol, quote):
    global last_quotes
    if symbol in last_quotes and quote["t"] == last_quotes[symbol]["t"]:
        logging.debug("Duplicate quote for " + symbol)
        return True
    else:
        last_quotes[symbol] = quote
        return False

def prep_request(symbols, auth_headers):
    return httpx.Request(
        'GET',
        QUOTES_URL,
        params={'symbols': ','.join(symbols)},
        headers=auth_headers
    )

async def poller(symbols, interval, auth_headers):
    request_ctr = prometheus_client.Counter('poll_requests', 'Number of HTTP requests')
    quote_ctr = prometheus_client.Counter('poll_quotes', 'Number of unique quotes')
    error_ctr = prometheus_client.Counter('poll_errors', 'Number of polling errors')
    prepped = prep_request(symbols, auth_headers)
    async with httpx.AsyncClient(http2=True) as client:
        while True:
            response = await client.send(prepped)
            request_ctr.inc()
            if (response.status_code == httpx.codes.ok):
                quotes = response.json()['quotes']
                for symbol in quotes.keys():
                    logging.info(f"Quote: {quotes[symbol]}")
                    if not is_dupe(symbol, quotes[symbol]):
                        kafka_pub.publish(symbol, 'quote', quotes[symbol])
                        quote_ctr.inc()
                kafka_pub.flush()
            else:
                logging.error('Error retrieving quotes: ' + response.text)
                error_ctr.inc()
            await asyncio.sleep(interval)
