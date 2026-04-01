FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY src/ ./src/

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]