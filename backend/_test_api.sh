#!/usr/bin/env bash
# Quick API test script
set -e

# Get admin token
TOKEN_JSON=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"Test@123"}')
TOKEN=$(echo "$TOKEN_JSON" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
echo "TOKEN: ${TOKEN:0:20}..."

echo ""
echo "=== 1. GET /api/candidates/ ==="
curl -s http://localhost:8000/api/candidates/ \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:500])"

echo ""
echo "=== 2. POST /api/screening/run ==="
curl -s -X POST http://localhost:8000/api/screening/run \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:500])"
