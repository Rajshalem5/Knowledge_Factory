# Deployment Guide

## Quick Start (Development)

```bash
# 1. Clone and setup
git clone <repo>
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 5. Setup database
createdb knowledge_factory
alembic upgrade head

# 6. Run server
python run.py
```

Visit: http://localhost:8000/docs

## Judge0 Setup

### Option 1: RapidAPI (Recommended for Development)

1. Go to https://rapidapi.com/judge0-official/api/judge0-ce
2. Subscribe to free tier (50 requests/day)
3. Copy API key to `.env`:
```
JUDGE0_API_KEY=your_key_here
```

### Option 2: Self-Hosted (Production)

```bash
# Using Docker
git clone https://github.com/judge0/judge0
cd judge0
docker-compose up -d

# Update .env
JUDGE0_API_URL=http://localhost:2358
JUDGE0_API_KEY=  # Leave empty for self-hosted
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Production Deployment

### Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t knowledge-factory-api .
docker run -p 8000:8000 --env-file .env knowledge-factory-api
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables (Production)

```bash
# Security
SECRET_KEY=<generate-strong-key>
ALGORITHM=HS256

# Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/knowledge_factory

# Judge0
JUDGE0_API_URL=https://your-judge0-instance.com
JUDGE0_API_KEY=<your-key>

# Performance
ASSESSMENT_DURATION_MINUTES=40
PASS_THRESHOLD=70.0
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# Development
tail -f logs/app.log

# Production (Docker)
docker logs -f <container-id>
```

## Performance Optimization

1. **Database Connection Pool**
```python
# In config.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

2. **Redis Caching** (Optional)
```python
# Cache question bank
redis_client.setex(f"questions:{candidate_id}", 3600, json.dumps(questions))
```

3. **Async Judge0 Calls**
Already implemented with `asyncio` and `httpx`

## Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Enable JWT authentication
- [ ] Validate all inputs
- [ ] Use environment variables
- [ ] Setup firewall rules
- [ ] Regular security updates

## Scaling

### Horizontal Scaling

```bash
# Run multiple instances behind load balancer
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_candidate_id ON assessments(candidate_id);
CREATE INDEX idx_assessment_status ON assessments(status);
CREATE INDEX idx_submission_assessment ON submissions(assessment_id);
```

## Troubleshooting

### Judge0 Connection Issues

```bash
# Test connection
curl -X POST "https://judge0-ce.p.rapidapi.com/submissions" \
  -H "X-RapidAPI-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"source_code":"print(1+1)","language_id":71}'
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U user -d knowledge_factory
```

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Backup & Recovery

```bash
# Backup database
pg_dump knowledge_factory > backup_$(date +%Y%m%d).sql

# Restore
psql knowledge_factory < backup_20240101.sql
```
