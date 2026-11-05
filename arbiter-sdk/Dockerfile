FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home --uid 10001 arbiter
COPY pyproject.toml README.md ./
COPY arbiter ./arbiter
RUN pip install --no-cache-dir .
USER arbiter
CMD ["python", "-c", "import arbiter; print(arbiter.__name__)"]
