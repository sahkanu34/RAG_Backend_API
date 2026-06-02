# Quick start script for RAG Backend (Windows PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RAG Backend - Quick Start Guide (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Python
$pythonTest = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python 3.9+ is required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Create virtual environment"
python -m venv venv

Write-Host "Step 2: Activate environment"
.\venv\Scripts\Activate.ps1

Write-Host "Step 3: Install dependencies"
pip install -r requirements.txt -q

Write-Host ""
Write-Host "Step 4: Setup external services" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option A: Using Docker Compose (recommended)" -ForegroundColor Green
Write-Host "  docker-compose up -d"
Write-Host ""
Write-Host "Option B: Manual Docker commands" -ForegroundColor Green
Write-Host "  - Redis:  docker run -d -p 6379:6379 redis:7"
Write-Host "  - Qdrant: docker run -d -p 6333:6333 qdrant/qdrant"
Write-Host ""

Write-Host "Step 5: Configure environment" -ForegroundColor Yellow
Write-Host "  copy .env.example .env"
Write-Host "  # Edit .env and add your OpenAI API key"

Write-Host ""
Write-Host "Step 6: Start the server" -ForegroundColor Yellow
Write-Host "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host ""
Write-Host "API Documentation:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs"
Write-Host ""
Write-Host "Health Check:" -ForegroundColor Cyan
Write-Host "  curl http://localhost:8000/health"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
