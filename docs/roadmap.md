# Roadmap

This file says what Arbiter does today and what work comes next. Read it
before you open a feature issue.

Sentences in this file use controlled technical English. One idea per
sentence. Active voice.

## What Arbiter Does Today

The API stores runs, task instances, DAGs and alerts. An owner creates API
keys and resolves alerts. A viewer reads data. Sign-in uses Argon2 hashed
passwords, access tokens and refresh tokens. Write routes have rate limits.

The API ingests one run with `POST /api/v1/runs` and many runs with
`POST /api/v1/runs/ingest`. Ingest creates a `failure` alert in the same
request. See `docs/adr.md`, ADR-001.

Celery Beat runs `check_stale_pipelines` every 10 minutes. That task creates
one `no_run` alert for each pipeline with no run in the last
`stale_pipeline_hours` hours. The default is 24 hours.

The dashboard shows the overview, the pipeline list, one DAG, the task
timeline, metrics, alerts and API keys. It runs on Next.js with NextAuth.

The SDK reports a run with the `Arbiter.monitor` decorator or with
`ArbiterClient.send_run`. The collector reads metadata from Airflow only.

Docker Compose starts PostgreSQL, Redis, the API, the Celery worker, Celery
Beat and the dashboard. CI checks the API, the packages and the dashboard on
every push.

## What Arbiter Does Not Do Yet

- Arbiter does not tell anyone about an alert. Alerts stay in the database
  until a person opens the dashboard.
- Arbiter does not compare a run duration with a limit. `AlertType` has the
  value `duration_exceeded`, but no code creates that alert.
- One global setting controls freshness. A pipeline that runs hourly and a
  pipeline that runs weekly share the same `stale_pipeline_hours` value.
- Arbiter has no routes for users. Scripts create the first users. A running
  installation cannot add, disable or remove a user.
- Arbiter does not delete old data. The `pipeline_runs` and `task_instances`
  tables only grow.
- No job publishes `arbiter-sdk`. Users install it from source.
- The collector supports Airflow only.

## Work In Review

Two pull requests change the base. Do not start work that depends on them
until they merge into `develop`.

- PR #226 adds a per-pipeline duration limit and the `duration_exceeded`
  alert.
- PR #227 adds the run browser and filters for runs, pipelines and alerts.

## Next Work

The list is ordered. Item 1 has the largest effect on daily use.

### 1. Alert notifications

**Problem.** A team must open the dashboard to learn that a pipeline failed.
That delay can be hours.

**Change.** Add notification channels for one organisation. Send each new
alert to every channel. Retry a failed send. Show the channels and their
delivery state in the dashboard.

**Done when.** A failed run causes one HTTPS POST to a test endpoint within
one worker cycle. The dashboard shows that delivery and its response code.
Repeating the same alert does not create a second open alert. Deleting a
channel stops its sends. `docs/api-integration.md` documents the payload and
the signature header.

### 2. Per-pipeline freshness budget

**Problem.** One global `stale_pipeline_hours` value fits every schedule
badly. It alerts too late for hourly pipelines and too early for weekly
pipelines.

**Change.** Let an owner set an expected interval, in hours, on each
pipeline. Keep the global value as the default for a pipeline with no
interval. Use the pipeline value in `check_stale_pipelines`.

**Done when.** Two pipelines with different intervals get correct `no_run`
alerts in one worker cycle. The API accepts and returns the interval. The
pipeline page shows it and edits it. Migration 0010 or later adds the column
with a null default.

### 3. Data retention

**Problem.** Installations accumulate runs forever. The tables grow without
limit and the queries slow down.

**Change.** Add a setting for a retention period in days. Add a periodic
Celery task that deletes runs older than that period. Cascade the delete to
task instances. Keep the alert history.

**Done when.** A test shows that a run older than the period is gone and a
newer run is present. The task reports the number of deleted runs. The
setting default keeps every run, so an upgrade changes nothing.

### 4. User and organisation management

**Problem.** An owner cannot add a teammate or remove a departed user.
Operations need scripts and direct database access.

**Change.** Add routes and a dashboard page for users. An owner invites a
user, sets a role and disables an account. Keep passwords hashed with Argon2.

**Done when.** An owner creates a viewer account in the dashboard. That
viewer signs in and sees only the organisation data. A disabled account
cannot sign in and cannot use an existing token.

### 5. More collectors

**Problem.** Teams that use another scheduler cannot reuse their metadata.
They write their own sender.

**Change.** Add a collector for one more scheduler. Pick the scheduler that
contributors ask for most. Keep the Airflow collector unchanged.

**Done when.** The new collector sends one run per completed job to the API.
Its tests cover run mapping and task mapping. `docs/api-integration.md`
explains the setup.

### 6. Packaging and release

**Problem.** Users install `arbiter-sdk` from a git checkout. There is no
published version and no release notes.

**Change.** Publish `arbiter-sdk` to PyPI on a version tag. Keep a tagged
release for the API image and the dashboard build. Fill the release notes
from `CHANGELOG.md`.

**Done when.** `pip install arbiter` installs a published version. A tag
triggers the publish job. The job fails when the tests fail.

## Later Ideas

- Uptime and success-rate reports per pipeline, over a chosen period.
- Comparison of one run with the previous runs of the same pipeline.
- Storage and display of task log text from the `log_output` column.
- Bulk reprocess of past runs after an alert rule changes.
- Sign-in with an identity provider, such as OIDC or SAML.
- Per-user notification preferences, so each person chooses their channels.
- Deployment of Arbiter on Kubernetes with a Helm chart.

## Non-Goals

- Arbiter does not orchestrate, schedule or run jobs.
- Arbiter does not become a general APM or log platform.
- Arbiter does not keep a fork of Airflow or of any other scheduler.
- This repository does not host a managed Arbiter service.

## How To Change This Roadmap

1. Open an issue. Describe the problem and who has it.
2. Discuss the scope in that issue.
3. Open a pull request that changes this file. Move the item, add it, or
   remove it.
4. Put a design decision in `docs/adr.md`, not in this file.

An item needs a "Done when" list before work starts. Keep each entry short.
Write the acceptance test first when the item is small.
