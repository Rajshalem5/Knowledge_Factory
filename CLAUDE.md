# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge Factory is a role-based intern hiring platform with AI-powered assessments, real-time code execution, and comprehensive analytics. It consists of:

- **Frontend**: React 19 + TypeScript + Vite SPA with role-based routing
- **Backend**: FastAPI + SQLAlchemy 2.0 async with PostgreSQL/SQLite
- **Key Features**: Multi-role access (candidate/hr/interviewer/admin/superadmin), assessment engine, code sandbox, proctoring, analytics

## Development Commands

### Frontend (React + Vite)
```bash
cd app
npm install              # Install dependencies
npm run dev             # Start dev server (http://localhost:5173)
npm run build           # TypeScript check + production build
npm run lint            # Run ESLint
npm run preview         # Preview production build
```

### Backend (FastAPI + Python)
```bash
cd backend
python -m venv venv                    # Create virtual environment
source venv/bin/activate               # Activate (Windows: venv\Scripts\activate)
pip install -r requirements.txt       # Install dependencies
alembic upgrade head                   # Run database migrations
uvicorn app.main:app --reload --port 8000  # Start dev server (http://localhost:8000)
pytest tests/                          # Run tests
```

### Database Operations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                             # Apply migrations
alembic downgrade -1                             # Rollback one migration
```

## Architecture Overview

### Frontend Architecture
- **SPA with client-side routing** using React Router v7
- **State management**: React Context for auth/theme, TanStack Query for server state
- **API layer**: Centralized `api` client with auto JWT injection from `localStorage.kf_token`
- **Role-based access**: `ProtectedRoute` component wraps protected routes, checks `useAuth().role`
- **Design system**: Tailwind CSS 4.2 with custom surface hierarchy and glassmorphism

### Backend Architecture
- **Clean architecture**: Routes → Services → Models → Schemas
- **Feature-based organization**: Each domain (auth, candidates, assessments, etc.) has its own module
- **Async/await throughout**: SQLAlchemy 2.0 async with PostgreSQL/SQLite
- **JWT authentication**: Role-based access control enforced at route level
- **Dependency injection**: FastAPI `Depends()` for database sessions and auth

### Key Architectural Patterns

**Frontend API Client Pattern**:
```typescript
// All API calls use the centralized api client
import { api } from './api/client';
const data = await api.get<CandidateType>('/candidates/:id');
```

**Backend Feature Structure**:
```
backend/app/features/{domain}/
├── models.py      # SQLAlchemy ORM models
├── schemas.py     # Pydantic request/response models
├── service.py     # Business logic layer
└── routes.py      # FastAPI route handlers
```

**Role-Based Access Control**:
- Frontend: `ProtectedRoute` component with `allowedRoles` prop
- Backend: Route-level decorators and dependency injection
- Roles: `candidate`, `hr`, `interviewer`, `admin`, `superadmin`

## Important Configuration

### Frontend Environment Variables (`app/.env`)
```env
VITE_API_URL=http://localhost:8000/api
VITE_ENABLE_DEMO_MODE=false
VITE_LOG_LEVEL=info
```

### Backend Environment Variables (`backend/.env`)
Key variables:
- `DATABASE_URL`: PostgreSQL or SQLite connection string
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `AI_API_KEY`: API key for AI question generation
- `SANDBOX_URL`: Code execution sandbox URL
- `CORS_ORIGINS`: Comma-separated allowed frontend origins

### Database Configuration
- **Development**: SQLite (`aiosqlite://`) works out of the box
- **Production**: PostgreSQL (`postgresql+asyncpg://`) recommended
- **Migrations**: Alembic with auto-discovery of all models inheriting from `Base`

## Key Development Patterns

### Adding a New Backend Feature
1. Create feature directory: `backend/app/features/{feature}/`
2. Implement models, schemas, service, routes following existing patterns
3. Import and register router in `backend/app/main.py`
4. Add models to `backend/app/main.py` startup event for discovery

### Adding a New Frontend Page
1. Create component in `app/src/pages/{section}/`
2. Add route in `app/src/App.tsx` with `ProtectedRoute` wrapper
3. Create API client functions in `app/src/api/{domain}.ts`
4. Create custom hook in `app/src/hooks/use{Domain}.ts` if needed

### Authentication Flow
1. User calls `login()` or `register()` from `AuthContext`
2. Backend validates credentials, returns JWT token + user data
3. Frontend stores `kf_token` and `kf_user` in `localStorage`
4. Subsequent API calls auto-include `Authorization: Bearer <token>` header
5. `ProtectedRoute` checks role and redirects unauthorized users

### API Error Handling
- Frontend: Centralized error handling in `api/client.ts` parses error responses
- Backend: Pydantic validation + custom exceptions in `app/core/exceptions.py`
- Consistent error format: `{"detail": "error message"}` or `{"message": "error message"}`

## Testing Approach

### Backend Testing
- **Framework**: pytest with pytest-asyncio for async tests
- **Fixtures**: Database session, async HTTP client in `tests/conftest.py`
- **Test isolation**: Each test runs in a transaction that's rolled back
- **Test database**: Separate `kf_test` database to avoid polluting dev data

### Frontend Testing
- Currently no test suite configured
- Consider adding React Testing Library for component tests
- Consider adding Playwright for E2E tests

## Common Issues and Solutions

### Frontend Issues
- **Blank page after login**: Check `ROLE_HOME_ROUTES` mapping in `app/src/utils/roles.ts`
- **401 on API calls**: Verify `localStorage.kf_token` exists and is valid
- **CORS errors**: Check `CORS_ORIGINS` in backend `.env` includes frontend URL
- **Build fails**: Run `npx tsc --noEmit` to see TypeScript errors

### Backend Issues
- **Database connection errors**: Verify `DATABASE_URL` format and database exists
- **Migration conflicts**: Use `alembic revision --autogenerate` carefully, review generated migrations
- **Import errors**: Ensure all models are imported in `app/main.py` startup event
- **Async/await errors**: All database operations must use async session and await

## Deployment Considerations

### Backend Deployment
- Use `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker` for production
- Set `DEBUG=false` in production environment
- Use PostgreSQL instead of SQLite for production
- Configure proper `JWT_SECRET_KEY` and other secrets
- Set up proper CORS origins for production frontend

### Frontend Deployment
- Build with `npm run build` for production
- Serve static files with nginx or similar
- Set `VITE_API_URL` to production backend URL
- Consider enabling HTTPS in production

## Code Quality Standards

### TypeScript/React
- Use TypeScript strict mode
- Follow existing component patterns and naming conventions
- Use TanStack Query for all server state
- Keep components focused and reusable
- Follow the established design system (colors, surfaces, typography)

### Python/FastAPI
- Use type hints throughout
- Follow async/await patterns for database operations
- Use Pydantic for all request/response validation
- Keep business logic in service layer, not in routes
- Use dependency injection for database sessions and auth

### Database
- All models inherit from `Base` in `app.database`
- Use Alembic for all schema changes
- Use async sessions for all database operations
- Follow naming conventions: snake_case for tables/columns

## Integration Points

### External Services
- **AI API**: Question generation via configured AI endpoint
- **Code Sandbox**: Judge0 or similar for code execution
- **Email Service**: SendGrid for email notifications
- **Object Storage**: S3-compatible for file uploads

### Key Integrations
- **Frontend ↔ Backend**: REST API with JWT authentication
- **Backend ↔ Database**: Async SQLAlchemy 2.0
- **Assessments ↔ Code Execution**: Sandbox integration for running code
- **Proctoring ↔ Frontend**: WebSocket or polling for real-time monitoring

## Performance Considerations

### Frontend
- TanStack Query caching with 30-second stale time
- Code splitting and lazy loading for large components
- Optimistic updates for better UX
- Debounced search and filter inputs

### Backend
- Async database operations for better concurrency
- Connection pooling configured in settings
- Rate limiting on sensitive endpoints
- Efficient database queries with proper indexing

## Security Notes

- JWT tokens stored in `localStorage` (consider httpOnly cookies for production)
- Role-based access control enforced on both frontend and backend
- Input validation via Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- CORS properly configured for allowed origins
- File upload validation and type checking
- Rate limiting on authentication and code execution endpoints