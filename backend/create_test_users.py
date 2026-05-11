"""
Create test users for all roles via Supabase Admin API.
Run this once to seed test accounts.
"""

import requests

SUPABASE_URL = "https://nwlfflecgukgfgdcyihk.supabase.co"
# Service role key — backend only, never in frontend
SERVICE_KEY = "sb_secret_f9ouhuuP_0zmm-5kF94ZkA_wpobqRGs"

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

USERS = [
    {
        "email": "superadmin@test.com",
        "password": "Test@1234",
        "full_name": "Super Admin",
        "role": "SUPERADMIN",
    },
    {
        "email": "admin@test.com",
        "password": "Test@1234",
        "full_name": "Admin User",
        "role": "ADMIN",
    },
    {
        "email": "hr@test.com",
        "password": "Test@1234",
        "full_name": "HR Manager",
        "role": "HR",
    },
    {
        "email": "candidate@test.com",
        "password": "Test@1234",
        "full_name": "Test Candidate",
        "role": "CANDIDATE",
    },
]


def create_user(user: dict) -> str | None:
    """Create user in Supabase Auth and return their UUID."""
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=HEADERS,
        json={
            "email": user["email"],
            "password": user["password"],
            "email_confirm": True,   # skip email verification
            "user_metadata": {
                "full_name": user["full_name"],
                "role": user["role"],
            },
            "app_metadata": {
                "role": user["role"],
            },
        },
    )

    if resp.status_code in (200, 201):
        uid = resp.json()["id"]
        print(f"  ✅ Created: {user['email']} (id: {uid})")
        return uid
    elif resp.status_code == 422 and "already" in resp.text.lower():
        # Already exists — get their ID
        list_resp = requests.get(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers=HEADERS,
        )
        for u in list_resp.json().get("users", []):
            if u["email"] == user["email"]:
                print(f"  ⚠️  Already exists: {user['email']} (id: {u['id']})")
                return u["id"]
    else:
        print(f"  ❌ Failed: {user['email']} — {resp.status_code} {resp.text[:100]}")
        return None


def insert_into_users_table(uid: str, user: dict):
    """Insert user into our custom users table via Supabase REST API."""
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/users",
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
        json={
            "id": uid,
            "email": user["email"],
            "password_hash": "managed_by_supabase",
            "full_name": user["full_name"],
            "role": user["role"],
            "status": "ACTIVE",
        },
    )
    if resp.status_code in (200, 201):
        print(f"  ✅ Inserted into users table: {user['role']}")
    else:
        print(f"  ⚠️  users table insert: {resp.status_code} {resp.text[:100]}")


def main():
    print("\n🚀 Creating test users...\n")
    print("=" * 50)

    for user in USERS:
        print(f"\n[{user['role']}] {user['email']}")
        uid = create_user(user)
        if uid:
            insert_into_users_table(uid, user)

    print("\n" + "=" * 50)
    print("\n✅ Done! Login credentials:\n")
    for user in USERS:
        print(f"  {user['role']:<15} {user['email']:<25} password: {user['password']}")
    print()


if __name__ == "__main__":
    main()
