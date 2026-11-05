FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home --uid 10001 arbiter
COPY pyproject.toml README.md ./
COPY collector ./collector
RUN pip install --no-cache-dir .
USER arbiter
ENTRYPOINT ["arbiter-collector"]
