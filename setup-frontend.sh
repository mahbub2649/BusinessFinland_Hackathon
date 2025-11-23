#!/bin/bash

# Smart Funding Advisor - Frontend Setup Script

echo "🎨 Setting up React Frontend with shadcn/ui..."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo "🎨 Dependencies installed successfully!"
echo ""
echo "🚀 To start the frontend:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "Frontend will be available at: http://localhost:3000"
echo ""
echo "Make sure the backend is running at: http://localhost:8000"