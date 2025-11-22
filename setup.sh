#!/bin/bash

echo "🚀 Smart Funding Advisor - Complete Setup"
echo "========================================"
echo ""

# Check requirements
echo "🔍 Checking requirements..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
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

# Setup Frontend
echo "🎨 Setting up React Frontend..."
echo "-------------------------------"

cd frontend

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install additional Tailwind dependencies
echo "📦 Installing Tailwind CSS..."
npm install -D tailwindcss@latest postcss@latest autoprefixer@latest

echo "✅ Frontend setup complete!"
cd ..

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
echo "2. Start Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🧪 To test the pipeline:"
echo "   python test_pipeline.py"
echo ""
echo "Happy hacking! 🚀"