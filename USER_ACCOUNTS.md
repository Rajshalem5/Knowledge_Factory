# 👥 **KNOWLEDGE FACTORY - USER ACCOUNTS GUIDE**

## **🔍 CHECK EXISTING USERS**

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Check what users exist
python check_users.py
```

---

## **🆕 CREATE TEST USERS**

Since this system uses **Supabase Authentication**, users must be created through:

### **Option 1: Frontend Registration (Recommended)**

1. **Start the application**:
   ```bash
   # Terminal 1: Backend
   cd backend && uvicorn app.main:app --reload --port 8000
   
   # Terminal 2: Frontend
   cd app && npm run dev
   ```

2. **Register users through UI**:
   - Go to: http://localhost:5173/register
   - Create accounts for different roles

### **Option 2: Supabase Dashboard**

1. **Access Supabase Dashboard**:
   - URL: https://supabase.com/dashboard/project/nwlfflecgukgfgdcyihk
   - Login with your Supabase account

2. **Create users in Authentication > Users**:
   - Click "Add user"
   - Set email, password, and metadata

---

## **🎭 RECOMMENDED TEST ACCOUNTS**

Create these accounts for testing different roles:

### **1. Super Admin**
```
Email: admin@knowledgefactory.com
Password: Admin123!
Role: SUPERADMIN
Name: System Administrator
```

### **2. HR Manager**
```
Email: hr@knowledgefactory.com
Password: HR123!
Role: HR
Name: HR Manager
```

### **3. Interviewer**
```
Email: interviewer@knowledgefactory.com
Password: Interview123!
Role: INTERVIEWER
Name: Technical Interviewer
```

### **4. Test Candidate 1**
```
Email: candidate1@student.edu
Password: Candidate123!
Role: CANDIDATE
Name: John Doe
College: MIT
Branch: Computer Science
CGPA: 8.5
```

### **5. Test Candidate 2**
```
Email: candidate2@student.edu
Password: Candidate123!
Role: CANDIDATE
Name: Jane Smith
College: Stanford
Branch: Software Engineering
CGPA: 9.2
```

---

## **📝 REGISTRATION STEPS**

### **For Each Test Account:**

1. **Go to Registration Page**:
   ```
   http://localhost:5173/register
   ```

2. **Fill the Form**:
   - **Name**: Full name
   - **Email**: Use emails from above
   - **Password**: Use passwords from above
   - **Role**: Will be set automatically or via dropdown

3. **Complete Registration**:
   - Click "Register"
   - Check for email verification (if enabled)
   - Login with credentials

### **Setting User Roles**

**Method 1: During Registration (if role selector exists)**
- Select role from dropdown during registration

**Method 2: Via Supabase Dashboard**
- Go to Authentication > Users
- Click on user
- Edit "User Metadata"
- Add: `{"role": "HR", "full_name": "HR Manager"}`

**Method 3: Via Database (Advanced)**
```sql
-- Update user role in Supabase SQL Editor
UPDATE auth.users 
SET raw_user_meta_data = raw_user_meta_data || '{"role": "HR"}'::jsonb
WHERE email = 'hr@knowledgefactory.com';
```

---

## **🔐 LOGIN CREDENTIALS SUMMARY**

| Role | Email | Password | Access |
|------|-------|----------|--------|
| **Super Admin** | admin@knowledgefactory.com | Admin123! | Full system access |
| **HR Manager** | hr@knowledgefactory.com | HR123! | Dashboard, candidates, analytics |
| **Interviewer** | interviewer@knowledgefactory.com | Interview123! | Interview panel, candidate details |
| **Candidate 1** | candidate1@student.edu | Candidate123! | Portal, assessments |
| **Candidate 2** | candidate2@student.edu | Candidate123! | Portal, assessments |

---

## **🧪 TESTING USER FLOWS**

### **1. Super Admin Flow**
```
Login → /superadmin → Manage organizations → Manage users
```

### **2. HR Flow**
```
Login → /dashboard → View candidates → /jobs → Create job → /selection → Select candidates → /analytics → View reports
```

### **3. Interviewer Flow**
```
Login → /interview → View assigned candidates → Submit feedback
```

### **4. Candidate Flow**
```
Login → /portal → View status → /assessment → Take coding test → View results
```

---

## **🔧 TROUBLESHOOTING**

### **Issue: "User not found" after registration**

**Cause**: User exists in Supabase Auth but not in local `users` table.

**Fix**: The backend should auto-create users on first login. Check `dependencies.py`:

```python
# In get_current_user() function
if not row:
    # First login — insert into our users table
    await db.execute(
        text("""
            INSERT INTO users (id, email, full_name, role, status, created_at, updated_at)
            VALUES (:id, :email, :full_name, :role, 'ACTIVE', now(), now())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": user_id, "email": email, "full_name": full_name, "role": role},
    )
```

### **Issue: "Role not recognized"**

**Cause**: Role not set in user metadata.

**Fix**: Update user metadata in Supabase dashboard:
```json
{
  "role": "HR",
  "full_name": "HR Manager"
}
```

### **Issue: "Cannot access certain pages"**

**Cause**: Role-based access control blocking access.

**Fix**: Check `ProtectedRoute` configuration in `App.tsx`:
```typescript
<Route path="/dashboard" element={
  <ProtectedRoute allowedRoles={['hr', 'admin', 'superadmin']}>
    <Dashboard />
  </ProtectedRoute>
} />
```

---

## **🚀 QUICK SETUP SCRIPT**

Create all test users at once:

```bash
# Create a script to register users via API
cat > create_test_users.sh << 'EOF'
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "Creating test users..."

# Super Admin
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@knowledgefactory.com",
    "password": "Admin123!",
    "full_name": "System Administrator",
    "role": "SUPERADMIN"
  }'

# HR Manager  
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "hr@knowledgefactory.com", 
    "password": "HR123!",
    "full_name": "HR Manager",
    "role": "HR"
  }'

# Interviewer
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "interviewer@knowledgefactory.com",
    "password": "Interview123!", 
    "full_name": "Technical Interviewer",
    "role": "INTERVIEWER"
  }'

# Test Candidates
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate1@student.edu",
    "password": "Candidate123!",
    "full_name": "John Doe", 
    "role": "CANDIDATE"
  }'

curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate2@student.edu",
    "password": "Candidate123!",
    "full_name": "Jane Smith",
    "role": "CANDIDATE" 
  }'

echo "Test users created!"
EOF

chmod +x create_test_users.sh
./create_test_users.sh
```

---

## **📋 VERIFICATION CHECKLIST**

After creating users, verify:

- [ ] ✅ Can login with each account
- [ ] ✅ Each role redirects to correct home page
- [ ] ✅ Role-based access control works
- [ ] ✅ User profile shows correct information
- [ ] ✅ Dashboard shows appropriate data for each role

---

**🎯 Start by running `python check_users.py` to see what users already exist, then create the missing ones through the frontend registration page.**