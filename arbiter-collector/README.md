# Arbiter Collector

The collector reads the run data of one Airflow instance and sends it to
Arbiter. Use the collector when you cannot put the SDK inside your jobs.

## Install

Run this command from the repository root:

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
  --arbiter-key arb_test_xxx \
  --interval 30
```

Each flag also has an environment variable, so you can leave it out. See
`.env.example` for the names.

## What the collector does

1. It asks Airflow for each DAG, its five most recent runs and the task
   instances of each run.
2. It sends that data to `POST /api/v1/runs/ingest`.
3. It sleeps for `--interval` seconds, then starts again.

Arbiter updates a run that it already has, so a repeated poll does not make
duplicate rows.

When a send fails, the collector waits 10 seconds, then twice that time, up to
300 seconds. After 12 failures in a row it stops for 600 seconds, then tries
again.

Do not put the Airflow password in the command line on a shared machine. Put it
in the environment instead.

Read the root README for the full Arbiter quickstart.
