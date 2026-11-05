# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

## Before Any Internet-Facing Deployment

The repository ships no production credentials, but a deployment is only as safe
as its `.env`. Before exposing Arbiter:

- Set `SECRET_KEY` to a real value (`openssl rand -hex 32`). The API refuses to
  boot with the built-in default when `ENVIRONMENT` is `staging` or `production`.
- Set `POSTGRES_PASSWORD` and the password inside `DATABASE_URL`; both compose
  files fail immediately if `POSTGRES_PASSWORD` is unset.
- Replace `NEXTAUTH_SECRET` with a freshly generated value.
- Run the dev seeds only locally (`RUN_SEEDS=true`); `docker-compose.prod.yml`
  overrides it to `false`. The seeded passwords and the collector API key are
  printed to the container log once, so never keep a log that contains them, and
  rotate any key you exposed.
- `seed_prod.py` creates users but never overwrites an existing password; change
  credentials in the product rather than by re-running the seed.

## Reporting a Vulnerability

Do NOT open a public issue. Send details to the repository owner via private
security advisory on GitHub. Review the [GitHub documentation][1] for how to
submit a security advisory.

You should receive a response within 48 hours. If the issue is confirmed,
a patch will be released as soon as possible.

[1]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability
