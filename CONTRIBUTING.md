# Contributing to Arbiter

## Development Setup

```sh
git clone https://github.com/felipemchdev/arbiter.git
cd arbiter
cp .env.example .env
docker compose up -d
```

## Project Structure

- `arbiter-api/` — FastAPI backend (Python 3.12+)
- `arbiter-dashboard/` — Next.js 14 frontend
- `arbiter-collector/` — Airflow polling agent
- `arbiter-sdk/` — Python instrumentation library

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

## Submitting Changes

1. Fork the repo and create a branch from `develop`
2. Write your changes; run `pytest` and `npm run build` before pushing
3. Open a pull request targeting `develop`
4. Ensure CI passes

## Code Style

- Python: follow PEP 8; type hints required on all public functions
- TypeScript: no implicit `any`; use inline styles (Tailwind only for utilities)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
