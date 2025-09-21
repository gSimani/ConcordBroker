#!/bin/bash
# Railway startup script
cd apps/api
python -m uvicorn property_live_api:app --host 0.0.0.0 --port $PORT --workers 1