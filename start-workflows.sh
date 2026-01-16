#!/bin/bash
# Super Simple Workflow Automation Startup Script

echo "🚀 Starting RestorationOS Workflow Automation..."
echo ""

# Step 1: Install dependencies (if needed)
echo "📦 Step 1: Installing dependencies..."
pip install -q fastapi uvicorn motor python-dotenv openai google-generativeai pydantic

# Step 2: Set environment variables
echo "🔧 Step 2: Setting up environment..."
export MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
export DB_NAME="${DB_NAME:-restorationos}"
export JWT_SECRET="${JWT_SECRET:-your-secret-key-here}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"

# Step 3: Start the server
echo "▶️  Step 3: Starting server on http://localhost:8000"
echo ""
echo "✅ Workflow Automation API will be available at:"
echo "   http://localhost:8000/api/workflows"
echo ""
echo "📚 Open your browser to access the UI"
echo ""

cd /home/user/GetwaveS201/backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
