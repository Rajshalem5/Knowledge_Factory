# Frontend-Backend Integration - Quick Reference

## 🎯 Key Files Changed

| File | Purpose | What Changed |
|------|---------|--------------|
| `src/api/client.ts` | HTTP client | Uses VITE_API_URL, auto JWT token attachment |
| `src/api/auth.ts` | Auth API calls | All 7 endpoints connected to backend |
| `src/contexts/AuthContext.tsx` | Auth state | Login/logout/refresh fully implemented |
| `src/types/index.ts` | Type definitions | Removed tenant_id, updated roles |
| `src/api/candidates.ts` | Candidates API | Full CRUD operations connected |
| `.env.example` | Environment template | Created with API URL config |

---

## 🔌 Backend Endpoints Map

| Frontend Call | Backend Endpoint | Description |
|--------------|------------------|-------------|
| `authApi.login()` | `POST /api/auth/login` | User login |
| `authApi.register()` | `POST /api/auth/register` | User registration |
| `authApi.logout()` | `POST /api/auth/logout` | Logout |
| `authApi.refreshToken()` | `POST /api/auth/refresh` | Refresh access token |
| `authApi.verifyOtp()` | `POST /api/auth/verify-otp` | OTP verification |
| `authApi.forgotPassword()` | `POST /api/auth/forgot-password` | Request reset link |
| `authApi.resetPassword()` | `POST /api/auth/reset-password` | Reset password with token |
| `authApi.getMe()` | `GET /api/auth/me` | Get current user |
| `candidatesApi.getAll()` | `GET /api/candidates` | List candidates |
| `candidatesApi.getById()` | `GET /api/candidates/:id` | Get candidate details |
| `candidatesApi.updateStatus()` | `PATCH /api/candidates/:id/status` | Update status |
| `candidatesApi.bulkUpload()` | `POST /api/candidates/bulk-upload` | CSV upload |

---

## 💻 Common Patterns

### 1. Protected Route
```tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

function Protected({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}
```

### 2. Role-Based Access
```tsx
import { useAuth } from './contexts/AuthContext';

function AdminOnly() {
  const { hasRole } = useAuth();
  
  if (!hasRole(['admin', 'superadmin'])) {
    return null;
  }
  
  return <AdminPanel />;
}
```

### 3. Data Fetching with Error Handling
```tsx
import { useEffect, useState } from 'react';
import { candidatesApi } from './api/candidates';

function CandidateList() {
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const response = await candidatesApi.getAll();
        setData(response.data);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
  }, []);

  if (error) return <div>Error: {error}</div>;
  return <ul>{data.map(c => <li key={c.id}>{c.name}</li>)}</ul>;
}
```

### 4. Form Submission
```tsx
import { useState } from 'react';
import { authApi } from './api/auth';

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  async function handleSubmit(e) {
    e.preventDefault();
    await authApi.login({ email, password });
    // User is now logged in
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={e => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button>Login</button>
    </form>
  );
}
```

---

## 🔑 Token Structure (New Format)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "HR"
  }
}
```

**Key Changes:**
- ❌ No more `tenant_id` 
- ✅ Simpler structure: `{id, email, name, role}`
- ✅ Password hashing upgraded to Argon2

---

## 📝 Environment Setup

1. Create `.env` file in `app/` directory:
   ```bash
   cp .env.example .env
   ```

2. Update API URL:
   ```bash
   VITE_API_URL=http://localhost:8000
   ```

3. Start dev server:
   ```bash
   cd app
   npm run dev
   ```

---

## ⚡ Quick Commands

### Test Authentication
```bash
# Login test
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@knowledgefactory.io","password":"Admin@12345"}'

# Verify OTP (dev mode accepts any 6-digit)
curl -X POST http://localhost:8000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@knowledgefactory.io","otp":"123456"}'
```

### Seed Database
```bash
cd backend
uvicorn app.main:app --reload
# System will auto-seed on first startup
```

---

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `Tenant not found` error | Remove all tenant_id references in frontend code |
| CORS errors | Add frontend origin to `CORS_ORIGINS` in backend config |
| Token expired | Call `authApi.refreshToken(refreshToken)` |
| Wrong API URL | Check `.env` file and restart dev server |
| 401 Unauthorized | Verify token in localStorage before making requests |

---

## 🧪 Testing Checklist

- [ ] Login works with valid credentials
- [ ] Registration creates new candidate
- [ ] Logout clears local storage
- [ ] Token refresh works when expired
- [ ] Protected routes redirect to login
- [ ] Role checks work correctly
- [ ] Candidates list displays data
- [ ] Profile page shows current user

---

## 📞 Need Help?

- **Full docs:** `FRONTEND_INTEGRATION.md`
- **Backend docs:** Open `/docs` at localhost:8000
- **Types:** See `app/src/types/index.ts`
- **API client:** See `app/src/api/client.ts`

---

**That's it!** Your frontend is now fully integrated with the modern single-tenant backend system. 🎉
