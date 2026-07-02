"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api import documents, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    print("Database initialized")
    
    yield
    
    # Shutdown
    print("Application shutting down")


app = FastAPI(
    title="NEURAL RAG Backend API v2.0",
    description="Conversational RAG system with document ingestion and interview booking",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Backend API"
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "NEURAL RAG Backend API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
