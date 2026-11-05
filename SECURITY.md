# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

## Before You Expose Arbiter to the Internet

This repository has no production credentials. Your `.env` decides if a
deployment is safe. Do each item below before you make Arbiter reachable from
the internet:

- Set `SECRET_KEY` to a real value. Run `openssl rand -hex 32` to make one. When
  `ENVIRONMENT` is `staging` or `production`, the API does not start with the
  built-in default key.
- Set `POSTGRES_PASSWORD`. Put the same password in `DATABASE_URL`. Both compose
  files stop at once if `POSTGRES_PASSWORD` is not set.
- Set `NEXTAUTH_SECRET` to a new value.
- Use the dev seeds only on your own machine. Set `RUN_SEEDS=true` only for a
  local run.
- Delete the container logs that show a seeded password or the collector API key.
  The seed prints each value once, at boot. Rotate any key that another person
  could read.
- Do not use `seed_prod.py` to change a password. That script makes users, but it
  never overwrites a password that exists. Change the password in the product.

## Reporting a Vulnerability

Do not open a public issue. Send the details to the repository owner in a
private security advisory on GitHub. The [GitHub documentation][1] explains how
to submit one.

You will get a response within 48 hours. If the owner confirms the problem, they
will release a patch as soon as possible.

[1]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability
