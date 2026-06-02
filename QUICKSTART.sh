#!/bin/bash
# Quick start script for RAG Backend

echo "=========================================="
echo "RAG Backend - Quick Start Guide"
echo "=========================================="

# Check Python
if ! command -v python &> /dev/null; then
    echo "Error: Python 3.9+ is required"
    exit 1
fi

echo ""
echo "Step 1: Create virtual environment"
python -m venv venv

echo "Step 2: Activate environment"
source venv/bin/activate  # Linux/Mac
# Or: .\venv\Scripts\Activate.ps1  # Windows PowerShell

echo "Step 3: Install dependencies"
pip install -r requirements.txt

echo ""
echo "Step 4: Setup external services"
echo ""
echo "Option A: Using Docker Compose (recommended)"
echo "  docker-compose up -d"
echo ""
echo "Option B: Manual setup"
echo "  - Redis: docker run -d -p 6379:6379 redis:7"
echo "  - Qdrant: docker run -d -p 6333:6333 qdrant/qdrant"
echo ""

echo "Step 5: Configure environment"
echo "  cp .env.example .env"
echo "  # Edit .env and add your OpenAI API key"

echo ""
echo "Step 6: Start the server"
echo "  python -m uvicorn app.main:app --reload"

echo ""
echo "API Documentation:"
echo "  http://localhost:8000/docs"
echo ""
echo "Health Check:"
echo "  curl http://localhost:8000/health"
echo ""
echo "=========================================="
