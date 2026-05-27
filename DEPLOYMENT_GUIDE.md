# Deployment Guide

## Prerequisites
*   Docker & Docker Compose installed on the host machine.
*   Nginx or equivalent reverse proxy (Optional but recommended).
*   SSL Certificates for HTTPS.

## Docker Setup

### 1. Build and Run via Docker Compose
The platform is containerized for easy deployment.

```bash
# From the project root
docker-compose up --build -d
```

### 2. Ports Used
*   **Frontend:** `5173` (or `80` if configured in compose)
*   **Backend (Core):** `8000`
*   **Backend (AI Proctoring):** `8001`
*   **Database (PostgreSQL):** `5432`
*   **Cache (Redis):** `6379`

### 3. Environment Setup for Production
Create a `.env.production` file. Ensure the following critical changes are made compared to local development:
*   `DEBUG=False`
*   `DATABASE_URL` points to your managed PostgreSQL instance.
*   `CORS_ORIGINS` strictly lists your frontend domain (e.g., `https://hire.yourcompany.com`).
*   `JWT_SECRET_KEY` and `PROCTORING_JWT_SECRET` are cryptographically secure random strings.
*   Secure API Keys for OpenRouter/HuggingFace are injected.

### 4. Database Setup
Once the backend container is running, execute migrations:
```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed_db.py
```

### 5. Reverse Proxy Configuration (Nginx Example)
Configure Nginx to route traffic to the appropriate containers.

```nginx
server {
    listen 80;
    server_name hire.yourcompany.com;

    location / {
        proxy_pass http://localhost:5173; # Frontend
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://localhost:8000; # Core Backend
        proxy_set_header Host $host;
    }

    location /ws/proctor/ {
        proxy_pass http://localhost:8001; # AI Proctoring Service
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

## Deployment Checklist
- [ ] Database credentials secured.
- [ ] JWT Secrets rotated.
- [ ] CORS restricted to production domain.
- [ ] HTTPS enforced.
- [ ] Volume mounts established for persistent storage (`/uploads`, `/screenshots`).
- [ ] Piston Code Execution engine isolated or deployed securely.
