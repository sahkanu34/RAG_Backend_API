# RAG Backend - Complete Implementation

## Overview

This is a production-ready FastAPI backend implementing a custom Conversational RAG (Retrieval Augmented Generation) system with document ingestion, embedding generation, and interview booking extraction.

**Key Features:**
- ✅ Document Ingestion API (PDF/TXT)
- ✅ Two Chunking Strategies (Fixed-Size & Semantic)
- ✅ Embeddings Generation (OpenAI)
- ✅ Vector Database Integration (Qdrant/Pinecone)
- ✅ Custom RAG System (No RetrievalQAChain)
- ✅ Multi-turn Conversation with Redis Memory
- ✅ Interview Booking Extraction via LLM
- ✅ Production-Grade Code Architecture
- ✅ Full Type Hints & Pydantic Validation
- ✅ Error Handling & HTTP Status Codes

## Project Structure

```
Palm_Mind_Task/
├── app/
│   ├── api/                          # REST API Endpoints
│   │   ├── documents.py              # Document upload & list endpoints
│   │   ├── chat.py                   # Chat & booking endpoints
│   │   └── __init__.py
│   ├── core/                         # Core Configuration & Setup
│   │   ├── config.py                 # Settings management
│   │   ├── database.py               # SQLAlchemy setup
│   │   └── __init__.py
│   ├── models/                       # SQLAlchemy ORM Models
│   │   ├── database.py               # Document, Chunk, Booking, ChatSession
│   │   └── __init__.py
│   ├── services/                     # Business Logic
│   │   ├── vector_db.py              # Vector DB abstraction (Qdrant/Pinecone)
│   │   ├── chunking.py               # Text chunking strategies
│   │   ├── embeddings.py             # Embeddings generation
│   │   ├── ingestion.py              # Document processing pipeline
│   │   ├── chat_memory.py            # Redis-based chat memory
│   │   ├── rag.py                    # Custom RAG system
│   │   ├── booking.py                # Interview booking extraction
│   │   └── __init__.py
│   ├── schemas/                      # Pydantic Request/Response Models
│   │   ├── schemas.py                # All API schemas
│   │   └── __init__.py
│   ├── utils/                        # Utility Functions
│   │   ├── helpers.py                # Logging, text sanitization
│   │   └── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   └── __init__.py
├── requirements.txt                  # Python dependencies
├── .env                              # Environment variables (create from .env.example)
├── .env.example                      # Environment variables template
├── docker-compose.yml                # Docker services (Qdrant, Redis)
├── README.md                         # Comprehensive documentation
├── QUICKSTART.ps1                    # Windows quick start
├── QUICKSTART.sh                     # Linux/Mac quick start
├── validate.py                       # Code validation script
└── test_simple.py                    # Simplified tests
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server (8000)                    │
├──────────────────────┬──────────────────────────────────────┤
│ Document Ingestion   │    Conversational RAG API             │
│ ────────────────────├──────────────────────────────────────┤
│ POST /api/documents/ │ POST /api/chat/start                  │
│     upload           │ POST /api/chat/message                │
│ GET  /api/documents/ │ GET  /api/chat/history/{id}           │
│     list             │ DELETE /api/chat/session/{id}         │
└──────────┬───────────┴──────────────┬───────────────────────┘
           │                          │
    ┌──────▼──────┐      ┌────────────▼────────────┐
    │  Vector DB  │      │   Chat Memory (Redis)   │
    │  (Qdrant)   │      │   + Booking Storage     │
    └─────────────┘      └──────────────────────────┘
           ▲                           ▲
           │                           │
    ┌──────┴───────────────────────────┴──────┐
    │        SQL Database (SQLite)             │
    │  - Documents, Chunks, Bookings          │
    │  - Chat Sessions, Metadata              │
    └────────────────────────────────────────┘
```

## API Endpoints

### Document Ingestion

#### Upload Document
```bash
POST /api/documents/upload
Content-Type: multipart/form-data

Parameters:
- file: PDF or TXT file (required)
- chunking_strategy: "fixed" or "semantic" (optional, default: "fixed")

Response: 200 OK
{
  "document_id": 1,
  "filename": "example.pdf",
  "file_type": "pdf",
  "file_size": 50000,
  "chunks_created": 5
}
```

#### List Documents
```bash
GET /api/documents/list

Response: 200 OK
[
  {
    "id": 1,
    "filename": "example.pdf",
    "file_type": "pdf",
    "file_size": 50000,
    "uploaded_at": "2024-01-01T12:00:00"
  }
]
```

### Conversational RAG

#### Start Chat Session
```bash
POST /api/chat/start

Response: 200 OK
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Chat session started"
}
```

#### Send Message
```bash
POST /api/chat/message
Content-Type: application/json

Request:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What is in the documents?",
  "use_context": true
}

Response: 200 OK
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Based on the documents...",
  "role": "assistant",
  "retrieved_chunks": 3,
  "booking_extracted": false,
  "booking_status": null,
  "timestamp": "2024-01-01T12:00:00"
}
```

#### Get Chat History
```bash
GET /api/chat/history/{session_id}

Response: 200 OK
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "user",
      "content": "What is this about?",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "role": "assistant",
      "content": "This document discusses...",
      "timestamp": "2024-01-01T12:00:01"
    }
  ],
  "message_count": 2,
  "created_at": "2024-01-01T12:00:00"
}
```

#### Delete Session
```bash
DELETE /api/chat/session/{session_id}

Response: 200 OK
{
  "message": "Session deleted successfully"
}
```

## Technology Stack

### Web Framework
- **FastAPI** 0.104.1 - Modern async web framework
- **Uvicorn** 0.24.0 - ASGI server
- **Pydantic** 2.5.0 - Data validation with type hints

### Database & Storage
- **SQLAlchemy** 2.0.23 - ORM for SQL databases
- **SQLite** - Default (easily switch to PostgreSQL)
- **Redis** 5.0.1 - Session & chat memory storage

### Vector & Embeddings
- **Qdrant Client** 2.7.0 - Vector database (default)
- **Pinecone Client** 3.0.2 - Alternative vector database
- **OpenAI** 1.3.5 - LLM & embeddings API
- **text-embedding-3-small** - Embeddings model (1536-dim)

### Text Processing
- **PyPDF** 3.17.1 - PDF text extraction
- **pdfplumber** 0.10.3 - Advanced PDF parsing
- **langchain-text-splitters** 0.0.1 - Semantic text splitting

### Utilities
- **python-multipart** 0.0.6 - File upload handling
- **email-validator** 2.1.0 - Email validation

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- OpenAI API key
- Docker (recommended for Redis & Qdrant)

### Step-by-Step Installation

1. **Clone and Setup**
```bash
cd d:\Palm_Mind_Task
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# or: source venv/bin/activate  # Linux/Mac
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup Services** (Docker Compose)
```bash
docker-compose up -d
# Starts: Qdrant (http://localhost:6333), Redis (localhost:6379)
```

4. **Configure Environment**
```bash
copy .env.example .env  # Windows
# or: cp .env.example .env  # Linux/Mac

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

5. **Start Server**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access API**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Configuration

### Environment Variables (.env)

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# LLM (OpenAI)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Database
VECTOR_DB_TYPE=qdrant  # Options: qdrant, pinecone
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# SQL Database
DATABASE_URL=sqlite:///./rag_backend.db  # Or: postgresql://user:pass@localhost/rag_db

# Redis Chat Memory
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_CHAT_EXPIRY=86400  # 24 hours

# Chunking
CHUNK_SIZE=1000          # Characters
CHUNK_OVERLAP=200        # Characters
CHUNKING_STRATEGY=fixed  # Options: fixed, semantic

# RAG Configuration
TOP_K_RETRIEVAL=5        # Documents to retrieve
SIMILARITY_THRESHOLD=0.3 # Minimum similarity score
```

## Chunking Strategies

### Fixed-Size Chunking
- Splits text into fixed-size chunks (configurable overlap)
- **Pros**: Fast, deterministic, good for uniform processing
- **Cons**: May split sentences

```python
chunker = ChunkerFactory.create("fixed", chunk_size=1000, overlap=200)
chunks = chunker.chunk(text)
```

### Semantic Chunking
- Splits at sentence boundaries (respects semantic units)
- **Pros**: Better semantic coherence, respects sentences
- **Cons**: Slightly slower, variable chunk sizes

```python
chunker = ChunkerFactory.create("semantic", target_size=1000, overlap=200)
chunks = chunker.chunk(text)
```

## Interview Booking Extraction

Automatically extracts booking information using LLM analysis:

**Supported Information:**
- Full name
- Email address
- Preferred interview date (YYYY-MM-DD)
- Preferred interview time (HH:MM)
- Additional notes/requirements

**Example Conversation:**
```
User: "I'd like to schedule an interview"
User: "My name is Jane Smith and email is jane@example.com"
User: "Can we do it on 2024-01-15 at 14:30?"

Response:
{
  "booking_extracted": true,
  "booking_status": {
    "id": 1,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "date": "2024-01-15",
    "time": "14:30"
  }
}
```

## Code Quality

### Type Hints
All functions have complete type hints for type checking and IDE support:

```python
def chunk(self, text: str) -> List[str]:
    """Split text into chunks."""
```

### Validation
Pydantic models for all API requests/responses:

```python
class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    use_context: bool = True
```

### Error Handling
Comprehensive error handling with proper HTTP status codes:

```python
# 400 Bad Request - Invalid input
# 404 Not Found - Resource not found
# 500 Internal Server Error - Processing failed
# 503 Service Unavailable - External service unavailable

ErrorResponse:
{
  "detail": "Error description",
  "error_code": "OPTIONAL_CODE",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Code Organization
- **Separation of Concerns**: Services, models, schemas, APIs are separate
- **DRY Principle**: Reusable services and utilities
- **Factory Patterns**: For chunkers and vector DB clients
- **Lazy Initialization**: Services initialized on first use
- **Async Support**: FastAPI async endpoints for concurrency

## Testing & Validation

### Code Compilation
```bash
python -m py_compile app/**/*.py
```

### Simple Validation
```bash
python validate.py
```

### API Testing

**Upload Document:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@sample.pdf" \
  -F "chunking_strategy=fixed"
```

**Start Chat:**
```bash
curl -X POST "http://localhost:8000/api/chat/start"
```

**Send Message:**
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "What is in the documents?"
  }'
```

## Production Deployment

### Recommendations

1. **Use PostgreSQL** instead of SQLite:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/rag_db
   ```

2. **Use Managed Services**:
   - Pinecone for vector DB (instead of self-hosted Qdrant)
   - AWS ElastiCache for Redis
   - AWS RDS for PostgreSQL

3. **Security**:
   - Use environment secrets (AWS Secrets Manager, etc.)
   - Enable HTTPS/TLS
   - Implement API authentication (JWT, API keys)
   - Add rate limiting

4. **Monitoring**:
   - Add structured logging (JSON format)
   - Implement error tracking (Sentry)
   - Monitor API performance

5. **Deployment**:
   - Use containerization (Docker)
   - Deploy to cloud (AWS ECS, Google Cloud Run, etc.)
   - Use CI/CD pipelines

Example Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping  # Should return: PONG

# Start Redis with Docker
docker run -d -p 6379:6379 redis:7
```

### Qdrant Connection Error
```bash
# Check if Qdrant is running
curl http://localhost:6333/health  # Should return: {"status":"ok"}

# Start Qdrant with Docker
docker run -d -p 6333:6333 qdrant/qdrant
```

### OpenAI API Error
- Verify API key is correct
- Check API quota/balance
- Verify network connectivity
- Check OpenAI API status

### Database Locked (SQLite)
- SQLite is not ideal for production
- Switch to PostgreSQL for concurrent access
- Or use: `sqlite3 rag_backend.db "PRAGMA journal_mode=WAL;"`

## Performance Tips

1. **Chunk Size**: 500-1000 chars for balanced retrieval/latency
2. **TOP_K_RETRIEVAL**: 3-5 for quality vs latency
3. **Similarity Threshold**: 0.3-0.5 for precision
4. **Embeddings Model**: text-embedding-3-small (1536-dim) for speed

## License

MIT License

## Support

For issues or questions:
1. Check README.md and API documentation
2. Review error messages and logs
3. Visit http://localhost:8000/docs for API details
4. Check external service status (OpenAI, Qdrant, Redis)

---

**Build Status**: ✅ Complete
**Code Quality**: ✅ All modules compile
**Architecture**: ✅ Production-ready
**Documentation**: ✅ Comprehensive
