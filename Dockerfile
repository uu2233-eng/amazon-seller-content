# ============================================================
# FastAPI Backend — Cloud Run 部署镜像
# 轻量版：使用 Gemini API，不含 PyTorch (~300MB)
# ============================================================

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY src/ src/
COPY api/ api/
COPY config.yaml .

RUN mkdir -p output data

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

EXPOSE 8080

CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 2
