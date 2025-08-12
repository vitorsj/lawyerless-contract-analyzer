#\!/bin/bash

# Lawyerless Setup Script
# Run this script to set up the development environment

echo "🚀 Setting up Lawyerless Development Environment..."
echo ""

# Check if we're in the right directory
if [ \! -f "README.md" ] || [ \! -d "backend" ] || [ \! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the Lawyerless root directory"
    exit 1
fi

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Check if Python 3.13 is available
if \! command -v python3.13 &> /dev/null; then
    echo "⚠️  Python 3.13 not found, trying python3..."
    if \! command -v python3 &> /dev/null; then
        echo "❌ Python 3+ is required. Please install Python 3.13+"
        exit 1
    fi
    PYTHON_CMD=python3
else
    PYTHON_CMD=python3.13
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
$PYTHON_CMD -m venv venv_linux

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv_linux/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy .env.example if .env doesn't exist
if [ \! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit backend/.env and add your OpenAI API key\!"
    echo "   Get your API key from: https://platform.openai.com/api-keys"
    echo ""
fi

cd ..

# Frontend setup
echo "🌐 Setting up frontend..."
cd frontend

# Check if Node.js is available
if \! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Please install Node.js 18+"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d. -f1 | sed 's/v//')
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ is required. Current version: $(node -v)"
    exit 1
fi

# Install dependencies
echo "📥 Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup complete\!"
echo ""
echo "🔑 NEXT STEPS:"
echo "1. Edit backend/.env and add your OpenAI API key:"
echo "   LLM_API_KEY=sk-your-actual-key-here"
echo ""
echo "2. Start the backend server:"
echo "   cd backend"
echo "   source venv_linux/bin/activate"
echo "   python -m uvicorn app.main:app --reload"
echo ""
echo "3. In another terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Access the system:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🎉 Happy coding with Lawyerless\!"
