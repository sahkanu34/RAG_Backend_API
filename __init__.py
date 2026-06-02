"""RAG Backend API - Conversational AI with Document Ingestion

This project provides a production-ready FastAPI backend for:
1. Document Ingestion API - Upload PDFs/TXTs, extract text, apply chunking strategies, generate embeddings
2. Conversational RAG API - Multi-turn chat with context retrieval, interview booking extraction

Architecture:
- FastAPI for REST endpoints
- Qdrant/Pinecone for vector storage
- SQLAlchemy with SQLite for metadata
- Redis for chat session management
- OpenAI for embeddings and LLM
"""

__version__ = "1.0.0"
