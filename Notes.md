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



```
