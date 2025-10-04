#!/bin/bash
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGRhMzM0MTdmMjY2YjRmODRhYjA0MzIiLCJlbWFpbCI6ImxpdGVzaHBlcnVtYWxsYUBnbWFpbC5jb20iLCJmdWxsX25hbWUiOiJMaXRlc2ggUGVydW1hbGxhIiwiZXhwIjoxNzU5MTYwNDgxLCJpYXQiOjE3NTkxMzE2ODEsImlzcyI6ImluZnJhLW1pbmQiLCJhdWQiOiJpbmZyYS1taW5kLWFwaSIsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJqdGkiOiJXSmZuUTlYbmpHZy1GNFdQOU9lMl8wbmNHeXRsSFBUVUctUVJRc3BpT0tnIn0.Jf9qyX25tcrz-SnpsexVoxdSiLhd5WCMeQvkLB3-2mE"

echo "🔄 Restarting ShopSphere assessment workflow with proper payload:"
curl -X POST "http://localhost:8000/api/v1/assessments/68da35507f266b4f84ab0438/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"assessment_id":"68da35507f266b4f84ab0438"}' | python -m json.tool