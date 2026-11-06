# Contributing to Arbiter

## Development Setup

1. Clone the repository and enter the folder.
2. Copy `.env.example` to `.env`. Replace every `CHANGE_ME` value. Put the same
   password in `POSTGRES_PASSWORD` and in the `DATABASE_URL` of the `arbiter`
   user. The containers do not start when one of the two values is missing, and
   the API cannot reach PostgreSQL when they do not match.
3. Start the containers.

```sh
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter
cp .env.example .env
docker compose up -d
```

The `api` service runs the migrations and the seeds at start. Read the seeded
password in `docker compose logs api`.

## Project Structure

- `arbiter-api/` - the FastAPI backend. It needs Python 3.12 or newer.
- `arbiter-dashboard/` - the Next.js 14 frontend.
- `arbiter-collector/` - the agent that reads run data from Airflow.
- `arbiter-sdk/` - the Python library that reports runs.

## Running Locally Without Docker

```sh
# API
cd arbiter-api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Dashboard
cd arbiter-dashboard
npm install
npm run dev
```

The API needs a `DATABASE_URL`. For a local run, point it at a SQLite file.
Do not run the Celery worker without a Redis server.

## Submitting Changes

1. Fork the repository. Make a branch from `develop`.
2. Make your changes.
3. Run the tests for each package you changed. Use `make test` for
   `arbiter-api` and `pytest` in the other packages.
4. Run `make build` to build the dashboard.
5. Push your branch and open a pull request against `develop`.
6. Look at the CI result. Fix each check that fails.

Keep one pull request per topic. Write what changed and why in the description.

## Code Style

- Python: follow PEP 8. Put a type hint on each public function.
- TypeScript: do not use an implicit `any`. Use inline styles for components.
  Use Tailwind only for utility classes.

## License

When you contribute to Arbiter, you agree that the MIT License covers your
contribution.
