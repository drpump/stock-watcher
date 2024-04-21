# stock-watcher

Simple python script to get quotes and minute bars from Alpaca and publish them. Details:
* Quotes are retrieved by polling
* Bars are delivered aynchronously through websockets
* Quotes and bars are printed to stdout (log output goes to stderr)
* A FastAPI server is started on port 8004 (configurable), and prometheus metrics are accessible at `http://localhost:8004/metrics/`
* Quote and bar price/volume/size info is published via prometheus guages with symbol as label
* Prometheus counters for quote/bar/trade/error counts are also available
* If kafka is enabled (KAFKA_DISABLE unset), quotes and bars are published to kafka (set KAFKA_BOOTSTRAP)
* Only new quotes are published (i.e. if unchanged it is not published)

## To run:

First obtain API credentials for your alpaca account and set `ALPACA_SECRET` and `ALPACA_KEY` environment variables to your secret and key values respectively

### Local script

As a local pythons script
* [optional] create a venv and activate it
* `pip3 install -r requirements.txt`
* Configure STOCK_SYMBOLS, KAFKA_BOOTSTRAP or KAFKA_DISABLE and ALPACA_POLL_SECONDS environment variables if required (see below)
* `python3 main.py`

### Docker

```
$ docker pull drpump/stock-watcher
$ docker run -it -p 8004:8004 -e ALPACA_KEY=${ALPACA_KEY} -e ALPACA_SECRET=${ALPACA_SECRET} -e KAFKA_DISABLE='' drpump/stock-watcher
```

### k8s + kafka/prometheus

Suggest running locally first to confirm your credentials and connectivity are OK. 

1. Kafka (optional)
  1. Install strimzi kubernetes operator for kakfa and create a kafka cluster: see the [quickstarts](https://strimzi.io/quickstarts/), use cluster name `dev-cluster` if you want to minimise editing of manifests
  1. `kubectl apply -f manifests/kafk-topics.yaml`, modifying cluster name if desired
1. Prometheus (recommended but sometimes finicky to install)
  1. Install the prometheusstack, suggest using the [helm chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
  1. `kubectl applf -f manifests/stock-watcher`
1. Watcher app
  1. Create a k8s secret with these credentials: 
    `kubectl create secret generic alpaca-creds --from-literal=ALPACA_KEY=${ALPACA_KEY} --from-literal=ALPACA_SECRET=${ALPACA_SECRET}`
  1. Edit `manifests/stock-watcher.yaml` and set your STOCK_SYMBOLS, KAFKA_BOOTSTRAP and ALPACA_POLL_INTERVAL environment variables. If not using kafka, add a `KAFKA_DISABLE` variable.
  1. `kubectl apply -f manifests/stock-watcher.yaml

1. To see kafka output (replace boostrap url if required):
    `kubectl -n kafka run kafka-consumer -ti --image=quay.io/strimzi/kafka:0.40.0-kafka-3.7.0 --rm=true --restart=Never -- bin/kafka-console-consumer.sh --bootstrap-server dev-cluster-kafka-bootstrap:9092 --topic stock-quotes`

1. For prometheus/grafana:
  1. Open grafana and choose `Explore`
  1. Choose `prometheus` as the source
  1. In the query dialogue, set the metric to `quote_bid` and optionally filter by symbol
  1. Hey presto, you'll get a graph of the bid prices
  1. Optionally add another query for the `quote_ask` metric and see them plotted together

## Configuration

The app uses the following environment variables for config:

* STOCK_SYMBOLS
    Comma-separated list of symbols to poll/watch, no spaces permitted, default is `RMD,AAPL` (ResMed and Apple)
* ALPACA_KEY
    Your ALPACA API key
* ALPACA_SECRET
    Your ALPACA API secret
* KAFKA_BOOTSTRAP
    Kafka bootstrap host+port for publishing quotes to Kafka. Default is `dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092` (strimzi k8s cluster called `dev-cluster` in `kafka` namespace)
* KAFKA_DISABLE
    If set to any value, kafka will not be used. Quotes will be printed to stdout in JSON format and price + count
    metrics will still be accessible on the FastAPI endpoint.
* ALPACA_POLL_SECONDS
    Polling interval in seconds, default is 60s (same as Alpaca bars interval)
* SERVICE_PORT
    Port to use for HTTP serve prometheus metrics and livez/readyz (health) checks. Default is 8004. Retrieve metrics from `http://localhost:${SERVICE_PORT}/metrics/`.

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
