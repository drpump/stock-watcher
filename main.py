import api
import poll_watcher
import push_watcher
import logging
import os
import asyncio
import kafka_pub

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

def env_or_default(env_var, value):
    return value if not env_var in os.environ else os.environ[env_var]

def auth_headers():
    return 


async def main():
    interval = float(env_or_default('ALPACA_POLL_SECONDS', '60'))
    symbols = env_or_default('STOCK_SYMBOLS', 'RMD,AAPL').split(',')
    bootstrap = 'dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092' if not 'KAFKA_BOOTSTRAP' in os.environ else os.environ['KAFKA_BOOTSTRAP']
    enable = False if 'KAFKA_DISABLE' in os.environ else True
    port = int(env_or_default('SERVICE_PORT', '8004'))
    auth = {
        'APCA-API-KEY-ID': os.environ['ALPACA_KEY'], 
        'APCA-API-SECRET-KEY': os.environ['ALPACA_SECRET'] 
    }
    await kafka_pub.init(bootstrap, enable)
    async with asyncio.TaskGroup() as tg:
        prom = tg.create_task(api.serve(8004))
        pusher = tg.create_task(push_watcher.pusher(symbols, auth))
        poller = tg.create_task(poll_watcher.poller(symbols, interval, auth))

asyncio.run(main())