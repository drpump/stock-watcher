from kafka import KafkaProducer
import time
import os
import json
import logging


QUOTE_TOPIC="stock-quotes"
bootstrap = 'dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092' if not 'KAFKA_BOOTSTRAP' in os.environ else os.environ['KAFKA_BOOTSTRAP']
enabled = False if 'KAFKA_DISABLE' in os.environ else True
counts = {}

if enabled:
    producer = KafkaProducer(bootstrap_servers=bootstrap)

def quote_json(symbol, quote):
    global count
    counts[symbol] = counts[symbol]+1 if symbol in counts else 1
    return json.dumps({'symbol': symbol, 'quote': quote, 'retrieved': str(time.time()), 'seq': counts[symbol]})

def send_quote(symbol, quote):
    msg = quote_json(symbol, quote)
    if enabled:
        producer.send(
            QUOTE_TOPIC, 
            key=bytearray(symbol, 'utf-8'), 
            value=bytearray(msg, 'utf-8')
        )
    else:
        print(msg)

def flush():
    if enabled:
        producer.flush()

