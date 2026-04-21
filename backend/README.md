# Knowledge Factory Backend 🚀

Production-ready **FastAPI** backend for **Knowledge Factory** - a complete candidate assessment and hiring platform.

## ✨ Features

- **FastAPI + Async SQLAlchemy** (PostgreSQL)
- **JWT Authentication** with role-based access (Superadmin/HR/Interviewer/Candidate)
- **Clean Architecture**: Routes → Services → Models → Schemas
- **Assessment Engine** with secure code sandbox (Python/JS/Java/C++)
- **Resume Upload & Parsing**
- **OTP Email Verification**
- **Analytics Dashboards** & hiring funnel
- **File Upload** with validation
- **Alembic Migrations**

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── core/                # Config, security, DB
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic request/response
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── utils/               # OTP, file upload, code runner
│   └── db/                  # Base models & sessions
├── alembic/                 # Database migrations
├── requirements.txt
├── .env                     # Copy & configure
└── README.md
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env  # Create .env.example from .env template

# Database setup
alembic upgrade head

# Run server
uvicorn app.main:app --reload --port 8000
```

**API Docs**: http://localhost:8000/docs

## 🌐 API Endpoints

```
POST /api/auth/register      # User signup
POST /api/auth/login         # JWT tokens
POST /api/candidates/        # Create candidate
GET  /api/candidates/        # List with filters
POST /api/assessment/submit  # Code submission
GET  /api/analytics/dashboard # Metrics & funnel
```

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.115 |
| Database | PostgreSQL + Async SQLAlchemy |
| Auth | JWT + OAuth2 + bcrypt |
| Email | aiosmtplib + OTP |
| Files | python-magic + Pillow |
| Migrations | Alembic |
| Analytics | Pandas + NumPy |

## 📊 Role Permissions

| Role | Candidates | Assessments | Analytics |
|------|------------|-------------|-----------|
| Superadmin | ✅ Full | ✅ Full | ✅ Full |
| HR | ✅ Full | ✅ View | ✅ Org |
| Interviewer | 🔒 View | ✅ View | ❌ |
| Candidate | ❌ | ✅ Submit | ❌ |

## 🔒 Security Features

- JWT tokens (access + refresh)
- Role-based access control
- Rate limiting ready
- SQL injection protection
- File upload validation
- Docker sandbox for code execution

## 📧 Environment Variables

Required in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/kf_db
SECRET_KEY=your-very-long-random-secret-key
SMTP_USER=your-email@gmail.com
FRONTEND_URL=http://localhost:3000
```

## 🧪 Testing

```bash
pip install -r requirements-dev.txt  # If created
pytest tests/
```

## 🚀 Production Deployment

```bash
# Gunicorn + Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Docker deployment recommended
```

## 🤝 Contributing

1. Fork & clone
2. `pip install -r requirements.txt`
3. Create feature branch
4. Add tests
5. Submit PR

**Made with ❤️ using FastAPI best practices**

---

[Frontend](https://github.com/your-org/frontend) | [API Docs](http://localhost:8000/docs)

