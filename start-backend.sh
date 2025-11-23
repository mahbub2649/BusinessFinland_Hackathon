#!/bin/bash
# Start backend with Python 3.12 and xai-sdk support

echo "🚀 Starting Smart Funding Advisor Backend with x.ai integration..."
cd /backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000