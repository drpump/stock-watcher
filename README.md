# stock-watcher

Simple python script to get quotes and minute bars from Alpaca and publish them. Details:
* Quotes are retrieved by polling
* Bars are delivered aynchronously through websockets
* If kafka is enabled (KAFKA_DISABLE unset), quotes and bars are published to kafka (set KAFKA_BOOTSTRAP)
* Otherwise quotes and bars are printed to stdout
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
$ docker run -e ALPACA_KEY=${ALPACA_KEY} -e ALPACA_SECRET=${ALPACA_SECRET} -e KAFKA_DISABLE='' drpump/stock-watcher
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
