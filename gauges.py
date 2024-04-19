from prometheus_client import Counter, Gauge

bar_gauges = {
    "h": Gauge('bar_high', "Bar high price", ['symbol']),
    "l": Gauge('bar_low', "Bar low price", ['symbol']),
    "o": Gauge('bar_open', "Bar open price", ['symbol']),
    "c": Gauge('bar_close', "Bar close price", ['symbol']),
    "v": Gauge('bar_volume', "Bar volume", ['symbol'])
}

ASK_PRICE="ap"
BID_PRICE="bp"
ASK_SIZE="as"
BID_SIZE="bs"
quote_gauges = {
    ASK_PRICE: Gauge('quote_ask', "Quote ask price", ['symbol']),
    BID_PRICE: Gauge('quote_bid', "Quote bid price", ['symbol']), 
    ASK_SIZE: Gauge('quote_ask_size', "Quote ask size", ['symbol']),
    BID_SIZE: Gauge('quote_bid_size', "Quote bid size", ['symbol'])
}

def bar_gauge_update(symbol, message):
    for key in bar_gauges.keys():
        bar_gauges[key].labels(symbol).set(message[key])
    return

def quote_gauge_update(symbol, message):
    # always report bid/ask size
    for gauge in [ASK_SIZE, BID_SIZE]:
        quote_gauges[gauge].labels(symbol).set(message[gauge])
    # ignore zero price quotes
    for gauge in [ASK_PRICE, BID_PRICE]:
        if (message[gauge] != 0):
            quote_gauges[gauge].labels(symbol).set(message[gauge])
    return