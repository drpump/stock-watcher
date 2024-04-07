# stock-watcher
Simple python scripts to get quotes from Alpaca.

* `poll-watcher.py` uses the Alpaca REST API to poll for quotes 
* `sock-watcher.py` receives quotes asynchronously through the Alpaca websocket interface

Both use environment variables for config, specifically:

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
    Polling intercal for `poll-watcher.py` in seconds, default is 300s (5 minutes)
