#!/bin/bash
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGRhMzM0MTdmMjY2YjRmODRhYjA0MzIiLCJlbWFpbCI6ImxpdGVzaHBlcnVtYWxsYUBnbWFpbC5jb20iLCJmdWxsX25hbWUiOiJMaXRlc2ggUGVydW1hbGxhIiwiZXhwIjoxNzU5MTYwNDgxLCJpYXQiOjE3NTkxMzE2ODEsImlzcyI6ImluZnJhLW1pbmQiLCJhdWQiOiJpbmZyYS1taW5kLWFwaSIsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJqdGkiOiJXSmZuUTlYbmpHZy1GNFdQOU9lMl8wbmNHeXRsSFBUVUctUVJRc3BpT0tnIn0.Jf9qyX25tcrz-SnpsexVoxdSiLhd5WCMeQvkLB3-2mE"

echo "📊 ShopSphere Assessment Status:"
curl -X GET http://localhost:8000/api/v1/assessments/68da35507f266b4f84ab0438 \
  -H "Authorization: Bearer $JWT_TOKEN" | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'Status: {data[\"status\"]}')
print(f'Progress: {data[\"progress\"][\"progress_percentage\"]}%')
print(f'Current Step: {data[\"progress\"][\"current_step\"]}')
print(f'Completed Steps: {data[\"progress\"][\"completed_steps\"]}')
print(f'Recommendations Generated: {data[\"recommendations_generated\"]}')
print(f'Reports Generated: {data[\"reports_generated\"]}')
"

echo -e "\n🔄 Trying to restart workflow:"
curl -X POST "http://localhost:8000/api/v1/assessments/68da35507f266b4f84ab0438/start" \
  -H "Authorization: Bearer $JWT_TOKEN" | python -m json.tool