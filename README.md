# Arbiter

Arbiter is an open-source observability framework for data pipelines. It provides centralized tracking, monitoring, and analysis for data workflows across different orchestrators (like Apache Airflow) and custom data applications.

## Architecture

![Arbiter Architecture](/arbiter_architecture_diagram.svg)

## Features

* **Centralized Observability** - A Next.js based dashboard for full visibility into pipeline runs, task instances, and execution times.
* **Airflow Integration** - An out-of-the-box polling agent (`arbiter-collector`) to sync DAGs and task states seamlessly.
* **Python SDK** - Instrument custom data applications natively using `arbiter-sdk`.
* **Async Backend** - High-performance FastAPI backend leveraging Celery for background task processing.

## Quick Start

The platform requires Docker and Docker Compose.

1. Copy the example environment configuration:
   ```sh
   cp .env.example .env
   ```

2. Start the services:
   ```sh
   docker compose up -d
   ```

3. Access the platform:
   * Dashboard: `http://localhost:3000` (Login at `/login`)
   * API: `http://localhost:8000/api/v1/health`

## Project Structure

This monorepo consists of the following components:

* `arbiter-api`: Core backend handling ingestion and metadata storage (FastAPI, SQLAlchemy, Celery).
* `arbiter-dashboard`: Web interface for pipeline visualization (Next.js 14, Tailwind CSS).
* `arbiter-sdk`: Python client library for publishing pipeline events.
* `arbiter-collector`: Python agent for Airflow state extraction.

## Development

The backend relies on PostgreSQL and Redis, which are provisioned automatically via Docker Compose.

To test or develop the Python packages (`arbiter-sdk` and `arbiter-collector`) locally, you can install them in editable mode:
```sh
pip install -e ./arbiter-sdk
pip install -e ./arbiter-collector
```
