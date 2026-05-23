# Quick Reference: Auth System Changes

## 🔑 Key Changes at a Glance

### Token Structure (NEW)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "HR"          // ⚠️ No tenant_id!
  }
}
```

### Password Hashing
- **Algorithm**: Argon2-cffi (SHA256/bcrypt removed)
- **Migration**: All existing passwords must be re-hashed on next login

### Removed Features
- ❌ Multi-tenancy (`tenant_id` from everything)
- ❌ `HiringCycle.tenant_id` lookup
- ❌ User model tenant relationship

### New/Improved Endpoints
| Endpoint | What Changed |
|----------|--------------|
| `POST /api/auth/reset-password` | Now actually works with real validation |
| `POST /api/auth/forgot-password` | Generates tokens (email sending TODO) |
| `POST /api/auth/logout` | Returns 204 No Content |
| `POST /api/auth/verify-otp` | Issues tokens directly |
| `POST /api/auth/refresh` | Enhanced error handling |

---

## 🧪 Test Commands

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Test login (candidate)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@candidate.io","password":"Welcome@123"}'

# Test candidate registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Test Candidate",
    "email":"new@candidate.io",
    "password":"Welcome@123",
    "college":"ABC University",
    "branch":"CSE",
    "cgpa":8.5,
    "passed_out_year":2026,
    "language_choice":"english"
  }'

# Test OTP verification
curl -X POST http://localhost:8000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@knowledgefactory.io","otp":"123456"}'

# Test password reset
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@knowledgefactory.io"}'
```

---

## 📋 Frontend Migration Checklist

- [ ] Remove `tenant_id` from API request bodies
- [ ] Update token storage (keep sub, email, role only)
- [ ] Implement logout button → call `/api/auth/logout`
- [ ] Add refresh token retry logic for 401 errors
- [ ] Update "Me" endpoint response parsing
- [ ] Test forgot password flow end-to-end

---

## 🚨 Breaking Changes Alert

**Clients MUST update to:**
1. Expect `user.role` as string (not `.value`)
2. No longer receive `tenant_id` in responses
3. Use `instanceof Candidate` check instead of `hasattr(college)`

**Example React Hook Change:**
```javascript
// OLD
const { data } = await api.get('/auth/me');
const userId = data.user.id;
const tenantId = data.user.tenant_id;  // ⚠️ BREAKS

// NEW
const { data } = await api.get('/auth/me');
const userId = data.user.id;
const roleId = data.user.role;        // ✅ WORKS
```

---

## 🔍 Debugging Tips

### JWT Decode Issue
```python
from jose import jwt
payload = jwt.decode(token, secret, algorithms=["HS256"])
print(payload)  # Should show: {"sub":"...","email":"...","role":"..."}
```

### Argon2 Verification
```python
from argon2 import PasswordHasher
ph = PasswordHasher()
try:
    ph.verify(hash, plain_password)
    print("✓ Valid")
except:
    print("✗ Invalid")
```

---

## 📞 Support

For issues after refactor:
1. Check `AUTH_REFACTOR_SUMMARY.md` for details
2. Review database migration status
3. Confirm `argon2-cffi` installed in production
4. Verify JWT secret configuration
