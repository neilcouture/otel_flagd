#
# Running in Shell
#

```bash
export PYTHONPATH=/Users/neil/DropBox/SML-DSProjects/Projects/083-o11y-demo/otel_flagd

export OTELFL_LOCUST_URL=http://10.0.0.5:8080/loadgen
export OTELFL_FLAGD_URL=http://10.0.0.5:8080/feature
export OTELFL_PROMETHEUS_URL=http://10.0.0.5:9090
```


```bash
export PYTHONPATH=/home/rocky


otelfl fetch --url http://localhost:9090 --outfile ./somename.csv --minutes 5


sh scenarios/all_failures_Xmins.sh

# Prometheus (default, unchanged)
./scenarios/all_failures_Xmins.sh

# Datadog
DD_URL=http://localhost:8126 ./scenarios/all_failures_Xmins.sh
```

```bash

# 5 mins or 2 minutes test with datadog

export OTELFL_LOCUST_URL=http://10.0.0.5:8080/loadgen
export OTELFL_FLAGD_URL=http://10.0.0.5:8080/feature
export DD_URL=http://10.0.0.5:8126
sh ./scenarios/all_failures_5mins.sh


```


# Running on AWS:

```bash

export PYTHONPATH=/home/rocky

# prometheus
otelfl fetch --url http://localhost:9090 --outfile ./somename.csv --minutes 5

# datadog
otelfl fetch --use-dd --url http://localhost:8126 --outfile metrics.csv --minutes 5

```



