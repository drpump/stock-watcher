# stock-watcher

Simple python script to get quotes and minute bars from Alpaca and publish them. Details:
* Quotes are retrieved by polling
* Bars are delivered aynchronously through websockets
* Quotes and bars are printed to stdout (log output goes to stderr)
* A FastAPI server is started on port 8004 (configurable) 
* Prometheus metrics are accessible at `http://localhost:8004/metrics/`
* Prometheus counters for quote/bar/trade/error counts are also available
* Quote and bar price/volume/size info is published via prometheus guages with symbol as label
* If kafka is enabled (KAFKA_DISABLE unset), quotes and bars are published to kafka (set KAFKA_BOOTSTRAP)
metrics (subject to port setting)
* Only new quotes are published (i.e. if unchanged it is not published)

## To run:

As a local pythons script
* [optional] create a venv and activate it
* `pip3 install -r requirements.txt`
* Configure environment variables (see below)
* If using kafka, create kafka topics if not auto creating
    - If running kafka in k8s using strimzi, use the topic manifests in `manifests/` to create topics
* `python3 main.py`

Via docker:

```
$ docker pull drpump/stock-watcher
$ docker run -it -p 8004:8004 -e ALPACA_KEY=${ALPACA_KEY} -e ALPACA_SECRET=${ALPACA_SECRET} -e KAFKA_DISABLE='' drpump/stock-watcher
```

## Environment

Environment variables for config:

* STOCK_SYMBOLS
    Comma-separated list of symbols to poll/watch, no spaces permitted, default is `RMD,AAPL` (ResMed and Apple)
* ALPACA_KEY
    Your ALPACA API key
* ALPACA_SECRET
    Your ALPACA API secret
* KAFKA_BOOTSTRAP
    Kafka bootstrap host+port for publishing quotes to Kafka. Default is `dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092` (strimzi k8s cluster called `dev-cluster` in `kafka` namespace)
* KAFKA_DISABLE
    If set to any value, kafka will not be used. Quotes will be printed to stdout in JSON format. Intended primarily for troubleshooting without kafka, but you could feed it elsewhere. 
* ALPACA_POLL
    Polling interval in seconds, default is 60s (same as bars interval)
* SERVICE_PORT
    Port to use for HTTP serve prometheus metrics and livez/readyz (health) checks. Default is 8004. Retrieve metrics from `http://localhost:${SERVICE_PORT}/metrics`.

## Implementation and behaviour notes

* Alpaca free accounts can only access the IEX exchange. Quotes, bars and trades from this exchange are considerably 
  less frequent than for other exchanges. For example, RMD gets a new bar every 1-5 minutes on average trading days.
* Assuming you run a Prometheus server, you will configure the server to poll the price gauges every N seconds
  If there is no update since the last poll it gets the same value again. If there were multiple updates, it only 
  gets the last one in the period. 
* If you want to better reflect all updates in your analytics, Kafka + Flink will allow you to do near-real-time 
  analytics on all messages the data streams. You could also add the received messages to a time-series database 
  for more static analysis. 
* A zero price for ask/bid in the quote data means that there are no sellers/buyers, not that the price is zero, so 
  these values are not added to the corresponding prometheus price guages.
* The trades push feed is currently untested and has no prometheus guages.
