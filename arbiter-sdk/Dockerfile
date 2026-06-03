FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY arbiter ./arbiter
RUN pip install --no-cache-dir .
CMD ["python", "-c", "import arbiter; print(arbiter.__name__)"]