# Arbiter Collector

Airflow polling agent — extracts DAG states and pushes them to Arbiter.

## Install

```sh
pip install -e ./arbiter-collector
```

## Usage

```sh
arbiter-collector \
  --airflow-url http://airflow:8080 \
  --airflow-user admin \
  --airflow-pass admin \
  --arbiter-api http://api:8000 \
  --arbiter-key arb_xxx \
  --interval 30
```

See the root README for the full Arbiter quickstart.
