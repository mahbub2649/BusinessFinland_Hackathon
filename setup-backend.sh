#!/bin/bash

echo "🚀 Smart Funding Advisor - backend Setup"
echo "========================================"
echo ""

# Check requirements
echo "🔍 Checking requirements..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi


echo "✅ Requirements check passed!"
echo ""

# Setup Backend
echo "🐍 Setting up Python Backend..."
echo "--------------------------------"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo "✅ Backend setup complete!"
echo ""


echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🚀 To start the application:"
echo ""
echo "1. Start Backend (Terminal 1):"
echo "   source venv/bin/activate"
echo "   cd backend"
echo "   uvicorn main:app --reload --port 8000"
echo ""
echo "Happy hacking! 🚀"