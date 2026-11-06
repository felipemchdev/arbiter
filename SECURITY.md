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
  overrides it to `false`. The file also refuses to start unless you set
  `ARBITER_ADMIN_USER` and `ARBITER_ADMIN_PASSWORD`. A new production database
  therefore gets its first owner from that upsert.
- The seeds print the generated passwords and the collector API key to the
  container log once. Delete every log that holds them. Rotate every key they
  show, and reset every password they show, including the owner password that the
  dev seed made. A saved log, a backup, or a CI artefact keeps the secret
  readable after the database forgets it.
- `seed_prod.py` creates users but never overwrites an existing password; change
  credentials in the product rather than by re-running the seed.
- Register webhook channels only for endpoints you control. The API rejects a
  channel URL whose host is a local name or a non-public address. It checks the
  resolved address again before every send. A public name can still resolve to an
  internal address after that check, because the client resolves it once more for
  the connection. Run the worker in a network segment that cannot reach internal
  services. Prefer `https://` URLs: the alert body carries pipeline names, run
  ids and error text.
- Arbiter stores each channel signing secret in clear text, because the worker
  must compute the HMAC of every body. The API never returns that secret after
  creation. Rotate it by deleting the channel and creating it again.

## Reporting a Vulnerability

Do not open a public issue. Send the details to the repository owner in a
private security advisory on GitHub. The [GitHub documentation][1] explains how
to submit one.

You will get a response within 48 hours. If the owner confirms the problem, they
will release a patch as soon as possible.

[1]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability
