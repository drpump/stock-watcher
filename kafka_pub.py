from kafka import KafkaProducer
import time
import os
import json
import logging

QUOTE='quote'
TRADE='trade'
BAR='bar'

sequences = {BAR: {}, QUOTE: {}}
topics = {BAR: 'stock-bars', QUOTE: 'stock-quotes'}
producer = None
enabled = None

def init(bootstrap, enable):
    global producer, enabled
    enabled = enable
    if enabled:
        producer = KafkaProducer(bootstrap_servers=bootstrap)

def incr(symbol, datatype):
    global sequences
    if symbol in sequences[datatype]:
        sequences[datatype][symbol] += 1
    else:
        sequences[datatype][symbol] = 1
    return sequences[datatype][symbol]

def publish(symbol, datatype, data):
    msg = {'symbol': symbol, datatype: data, 'seq': incr(symbol, datatype)}
    if enabled:
        producer.send(
            topics[datatype], 
            key=bytearray(symbol, 'utf-8'), 
            value=bytearray(json.dumps(msg), 'utf-8')
        )
    else:
        print(json.dumps(msg))

def flush():
    if enabled:
        producer.flush()

