#!/bin/bash

# Knowledge Factory Backend Setup Script

echo "🚀 Setting up Knowledge Factory Backend..."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.12 or higher."
    exit 1
fi

echo "✅ Python found: $(python --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env 2>/dev/null || echo "DATABASE_URL=sqlite+aiosqlite:///./knowledge_factory.db" > .env
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate  (Linux/Mac)"
echo "     .\\venv\\Scripts\\activate  (Windows)"
echo ""
echo "  2. Test Piston integration:"
echo "     python test_piston_standalone.py"
echo ""
echo "  3. Start the server:"
echo "     uvicorn app.main:app --reload --port 8000"
echo ""
