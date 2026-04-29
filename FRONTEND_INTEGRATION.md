# Frontend Backend Integration - Complete Guide

## Overview

This document describes the integration between the frontend (React/Next.js) and backend (FastAPI) authentication systems.

---

## ✅ Changes Made

### 1. **API Client (`src/api/client.ts`)**
- ✅ Uses environment variable for base URL
- ✅ Auto-attaches JWT token to all requests
- ✅ Handles errors consistently
- ✅ Supports all HTTP methods (GET, POST, PUT, PATCH, DELETE)

### 2. **Auth API (`src/api/auth.ts`)**
**All endpoints connected:**
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/register` - Register new user/candidate
- `POST /api/auth/logout` - Logout endpoint
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/verify-otp` - OTP verification
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token
- `GET /api/auth/me` - Get current user profile

### 3. **Auth Context (`src/contexts/AuthContext.tsx`)**
**Features implemented:**
- ✅ Automatic login flow with state management
- ✅ Automatic logout with local storage cleanup
- ✅ Token refresh mechanism
- ✅ User data persistence in localStorage
- ✅ Role-based access control helper
- ✅ Error handling for auth failures

### 4. **Types Updated (`src/types/index.ts`)**
- ✅ Removed `tenant_id` from all models
- ✅ Removed `organizationId` from User interface
- ✅ Added role types: `'candidate' | 'hr' | 'admin' | 'superadmin' | 'interviewer'`
- ✅ Updated all interfaces to match backend response format

### 5. **Candidates API (`src/api/candidates.ts`)**
- ✅ Connected to `/api/candidates` endpoints
- ✅ Pagination support
- ✅ Filter by status, branch, college, search
- ✅ Bulk upload with FormData
- ✅ Status update endpoint

### 6. **Environment Setup**
Created `.env.example` with:
```bash
VITE_API_URL=http://localhost:8000
```

---

## 🚀 Usage Examples

### Using Auth Context

```tsx
import { useAuth } from './contexts/AuthContext';

function MyComponent() {
  const { 
    user,           // Current user object
    token,          // JWT token string
    isLoading,      // Loading state
    isAuthenticated,// Boolean flag
    login,          // Login function
    register,       // Register function
    logout,         // Logout function
    hasRole,        // Check if user has role
  } = useAuth();

  return (
    <div>
      {isAuthenticated ? (
        <p>Welcome, {user?.name}!</p>
      ) : (
        <button onClick={() => login('email@example.com', 'password')}>
          Login
        </button>
      )}

      {/* Role-based rendering */}
      {hasRole(['admin', 'superadmin']) && (
        <AdminPanel />
      )}
    </div>
  );
}
```

### Direct API Calls

```tsx
import { candidatesApi } from './api/candidates';

async function loadCandidates() {
  try {
    const response = await candidatesApi.getAll({
      page: 1,
      pageSize: 20,
      status: 'applied'
    });
    
    console.log(response.data); // Array of candidates
    console.log(response.pagination); // { page, limit, total, totalPages }
  } catch (error) {
    console.error('Failed to load candidates:', error);
  }
}
```

### Protected Routes Example

```tsx
import { useAuth } from './contexts/AuthContext';
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}
```

### Password Reset Flow

```tsx
import { useState } from 'react';
import { authApi } from './api/auth';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      const { message: msg } = await authApi.forgotPassword({ email });
      setMessage(msg);
    } catch (error) {
      console.error(error);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <button type="submit">Send Reset Link</button>
      {message && <p>{message}</p>}
    </form>
  );
}
```

---

## 🔧 Environment Configuration

### Step 1: Create `.env` file

In the `app` directory:
```bash
cd app
cp .env.example .env
```

### Step 2: Update API URL

Edit `app/.env`:
```bash
VITE_API_URL=http://localhost:8000
# Or production URL:
# VITE_API_URL=https://api.yourapp.com
```

### Step 3: Start development server

```bash
npm run dev
# or
pnpm dev
```

The vite build process will embed these values at build time.

---

## 📝 Type Mappings

### User Object Comparison

| Field | Old (Multi-Tenant) | New (Single-Tenant) | Status |
|-------|-------------------|---------------------|--------|
| `id` | ✅ UUID | ✅ UUID | Unchanged |
| `email` | ✅ String | ✅ String | Unchanged |
| `name` | ✅ String | ✅ String | Unchanged |
| `role` | ✅ Enum | ✅ String (lowercase) | Updated |
| `tenant_id` | ❌ Present | ✅ Removed | **REMOVED** |
| `organization_id` | ❌ Present | ✅ Removed | **REMOVED** |

### Response Format

**Old:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "HR",
    "tenant_id": "tenant-uuid"
  }
}
```

**New:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "HR"
  }
}
```

---

## 🎯 Role-Based Access Control

### Available Roles

```typescript
type Role = 'candidate' | 'hr' | 'admin' | 'superadmin' | 'interviewer';
```

### Checking Roles

```tsx
import { useAuth } from './contexts/AuthContext';

function AdminOnlyPage() {
  const { user, hasRole } = useAuth();

  // Method 1: Direct check
  if (hasRole(['admin', 'superadmin'])) {
    return <AdminDashboard />;
  }

  // Method 2: Component-level guard
  if (!hasRole(['admin', 'superadmin'])) {
    return <Navigate to="/" />;
  }

  // Method 3: JSX conditional
  {hasRole(['admin', 'superadmin']) && <AdminPanel />}
}
```

### Role Normalization

The `hasRole()` method handles:
- Case-insensitive comparison (`'ADMIN' === 'admin'`)
- Underscore conversion (`'SUPER_ADMIN' === 'superadmin'`)

---

## 🛡️ Security Considerations

### Token Storage
- Tokens stored in `localStorage` (client-side persistent)
- Best practice: Consider httpOnly cookies for sensitive apps
- Token automatically attached to all API requests

### Error Handling
```tsx
try {
  await authApi.login(email, password);
} catch (error) {
  const errorMessage = error instanceof Error ? error.message : 'Login failed';
  // Display friendly error to user
}
```

### CSRF Protection
- JWT tokens don't require CSRF tokens
- If using httpOnly cookies, add CSRF protection

---

## 🔍 Troubleshooting

### Issue: "Could not validate credentials"

**Cause:** Missing or invalid JWT token in request headers

**Solution:**
```tsx
// Verify token exists before making request
const token = localStorage.getItem('kf_token');
if (!token) {
  throw new Error('Not authenticated');
}
```

### Issue: "No active hiring cycle"

**Cause:** Backend requires active hiring cycle for candidate registration

**Solution:** Seed database with active cycle first:
```sql
INSERT INTO hiring_cycles (...) VALUES (...);
-- Ensure status = 'active'
```

### Issue: CORS errors when running frontend and backend locally

**Cause:** Backend CORS configuration doesn't allow frontend origin

**Solution:** Update `backend/app/main.py` or `.env`:
```python
# Add frontend origin to CORS origins
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

---

## 📦 Migration Checklist

Before deploying to production:

- [ ] Update `VITE_API_URL` to production backend URL
- [ ] Test all auth flows (login, register, logout, password reset)
- [ ] Verify token expiry and refresh works
- [ ] Update all protected routes to use `AuthProvider`
- [ ] Remove any hardcoded tenant references
- [ ] Test role-based access on all pages
- [ ] Verify bulk upload functionality
- [ ] Run E2E tests for critical user journeys

---

## 📚 Additional Resources

- **[Frontend API Files](./app/src/api/)** - All API client implementations
- **[Auth Context](./app/src/contexts/AuthContext.tsx)** - Centralized auth state management
- **[Backend API Docs](../backend/)** - FastAPI OpenAPI docs at `/docs`
- **[Type Definitions](./app/src/types/index.ts)** - All TypeScript interfaces

---

**Integration complete!** The frontend is now fully connected to the refactored backend with clean API calls, proper typing, and no multi-tenant complexity.
