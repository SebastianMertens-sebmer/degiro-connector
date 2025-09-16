#!/bin/bash
# Production startup script for DEGIRO Trading API

set -e

echo "🚀 Starting DEGIRO Trading API in Production Mode..."

# Check if config exists
if [ ! -f "config/config.json" ]; then
    echo "❌ Error: config/config.json not found!"
    echo "Please create your DEGIRO configuration file."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using default settings."
    echo "Copy .env.example to .env and configure for production."
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default API key if not provided
if [ -z "$TRADING_API_KEY" ]; then
    echo "❌ Error: TRADING_API_KEY environment variable is required!"
    echo "Set it in .env file or export TRADING_API_KEY=your-key"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, degiro_connector" || {
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
}

# Start the API with production settings
echo "🌟 Starting API server..."
echo "   API Key: ${TRADING_API_KEY:0:10}..."
echo "   Config: ${DEGIRO_CONFIG_PATH:-config/config.json}"
echo "   Docs: http://localhost:8000/docs"

# Use gunicorn for production or uvicorn for development
if command -v gunicorn &> /dev/null; then
    echo "   Using Gunicorn (production)"
    gunicorn api.main:app \
        --bind 0.0.0.0:8000 \
        --workers ${MAX_WORKERS:-4} \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --log-level ${LOG_LEVEL:-info}
else
    echo "   Using Uvicorn (development)"
    python3 api/main.py
fi