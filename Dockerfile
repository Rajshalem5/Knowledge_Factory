# KF Dockerfile — multi-stage build
# Backend (FastAPI) serves the React SPA via SPA fallback

# ── Stage 1: Build Frontend ──
FROM node:22-alpine AS frontend-builder

WORKDIR /app
COPY app/package.json app/package-lock.json ./
RUN npm ci

COPY app/ ./
RUN npm run build

# ── Stage 2: Build Backend ──
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system deps for argon2, aiosqlite, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/dist/ ./app/dist/

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
