"""
Debug JWT token validation issues
"""

import asyncio
import json
import base64
import httpx
from app.config import settings

async def debug_jwt_validation():
    """Debug JWT validation issues"""
    
    print("🔍 Debugging JWT validation...")
    print(f"📍 Supabase URL: {settings.SUPABASE_URL}")
    
    # 1. Fetch current JWKS from Supabase
    print("\n1️⃣ Fetching current JWKS from Supabase...")
    try:
        # Try different JWKS endpoints
        jwks_urls = [
            f"{settings.SUPABASE_URL}/.well-known/jwks.json",
            f"{settings.SUPABASE_URL}/auth/v1/jwks",
            f"{settings.SUPABASE_URL}/rest/v1/auth/jwks"
        ]
        
        current_jwks = None
        for url in jwks_urls:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    current_jwks = response.json()
                    print(f"✅ Found JWKS at: {url}")
                    print(json.dumps(current_jwks, indent=2))
                    break
                else:
                    print(f"❌ {url}: {response.status_code}")
        
        if not current_jwks:
            print("❌ Could not fetch JWKS from any endpoint")
            print("🔧 This might be why JWT validation is failing")
            return
            
    except Exception as e:
        print(f"❌ Error fetching JWKS: {e}")
        return
    
    # 2. Compare with hardcoded keys
    print("\n2️⃣ Comparing with hardcoded keys in dependencies.py...")
    
    hardcoded_jwks = {
        "keys": [
            {
                "alg": "ES256", "crv": "P-256", "kty": "EC", "use": "sig",
                "kid": "c1124293-620a-4d62-82b4-09c611cdda31",
                "x": "l9ntIqpDCJi-0EmvEvpsf52TqY-8Wy117i7mx297h-k",
                "y": "8qW_55T7nnXwMHZJ8OMBuuhRdLAjB-RDqj4Lif18s7Y"
            },
            {
                "alg": "ES256", "crv": "P-256", "kty": "EC", "use": "sig",
                "kid": "86e6341f-a281-4890-8070-328fbd9c42c5",
                "x": "NBNcBA42ZZ7_EeMep7e2V7FJBUPM9NJH5we6XQl_GvI",
                "y": "bWyArNlnzXldOO7T9Q8pviDwQ37NYDFeloDU7ZOUbFA"
            }
        ]
    }
    
    print("🔑 Hardcoded JWKS:")
    print(json.dumps(hardcoded_jwks, indent=2))
    
    # 3. Check if keys match
    current_kids = {key["kid"] for key in current_jwks["keys"]}
    hardcoded_kids = {key["kid"] for key in hardcoded_jwks["keys"]}
    
    print(f"\n3️⃣ Key ID comparison:")
    print(f"Current Supabase KIDs: {current_kids}")
    print(f"Hardcoded KIDs: {hardcoded_kids}")
    
    if current_kids == hardcoded_kids:
        print("✅ Key IDs match!")
    else:
        print("❌ Key IDs don't match!")
        print(f"Missing in hardcoded: {current_kids - hardcoded_kids}")
        print(f"Extra in hardcoded: {hardcoded_kids - current_kids}")
        
        print("\n🔧 SOLUTION: Update dependencies.py with current JWKS:")
        print("Replace _SUPABASE_JWKS with:")
        print(json.dumps(current_jwks, indent=2))
    
    # 4. Test token creation
    print("\n4️⃣ Testing token creation...")
    print("📝 To test:")
    print("1. Register a user in frontend")
    print("2. Check browser dev tools > Application > Local Storage")
    print("3. Copy the JWT token")
    print("4. Decode it at https://jwt.io to see the 'kid' field")
    print("5. Verify the 'kid' matches one of the current JWKS keys")

if __name__ == "__main__":
    asyncio.run(debug_jwt_validation())