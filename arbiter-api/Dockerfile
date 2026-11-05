FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 arbiter
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=arbiter:arbiter . .
COPY --chown=arbiter:arbiter entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER arbiter
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/api/v1/health || exit 1
CMD ["/entrypoint.sh"]
