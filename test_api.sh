#!/bin/bash

echo "🔐 Testing API Authentication and Data Loading..."
echo "=============================================="

# Login and get token
echo "1. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "liteshperumalla@gmail.com", "password": "Litesh@#12345"}' | \
  jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Login failed!"
    exit 1
else
    echo "✅ Login successful! Token: ${TOKEN:0:50}..."
fi

echo ""
echo "2. Testing user profile..."
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/profile | jq '.'

echo ""
echo "3. Testing assessments endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/assessments/ | jq '.'

echo ""
echo "4. Testing reports endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/reports/ | jq '.'

echo ""
echo "5. Testing scenarios endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/scenarios/ | jq '.'

echo ""
echo "✅ API testing complete!"