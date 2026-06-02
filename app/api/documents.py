"""Document ingestion API endpoints."""
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.schemas import DocumentUploadResponse, DocumentMetadata
from app.services.ingestion import DocumentIngestor
from app.services.chunking import ChunkerFactory
from app.services.embeddings import get_embeddings_generator
from app.services.vector_db import get_vector_db_client


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT file"),
    chunking_strategy: str = "fixed",
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload and ingest a document.
    
    Supports PDF and TXT files. Extracts text, applies chunking,
    generates embeddings, and stores in vector database and SQL database.
    
    Args:
        file: Uploaded file (PDF or TXT)
        chunking_strategy: 'fixed' or 'semantic'
        db: Database session
        
    Returns:
        DocumentUploadResponse with document details
        
    Raises:
        HTTPException: If file type unsupported or processing fails
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["pdf", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and TXT files supported"
            )
        
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Initialize services
        chunker = ChunkerFactory.create(
            chunking_strategy,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        
        embeddings_gen = get_embeddings_generator(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL
        )
        
        vector_db = get_vector_db_client(
            db_type=settings.VECTOR_DB_TYPE,
            url=settings.QDRANT_URL if settings.VECTOR_DB_TYPE == "qdrant" else None,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )
        
        ingestor = DocumentIngestor(
            db=db,
            chunker=chunker,
            embeddings_generator=embeddings_gen,
            vector_db_client=vector_db,
        )
        
        # Process document
        if file_ext == "pdf":
            doc = ingestor.ingest_pdf(content, file.filename)
        else:
            doc = ingestor.ingest_text(content, file.filename)
        
        # Count chunks
        from app.models.database import Chunk
        chunk_count = len(db.query(Chunk).filter(Chunk.document_id == doc.id).all())
        
        return DocumentUploadResponse(
            document_id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            chunks_created=chunk_count,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/list", response_model=list[DocumentMetadata])
async def list_documents(db: Session = Depends(get_db)) -> list[DocumentMetadata]:
    """List all uploaded documents.
    
    Returns:
        List of DocumentMetadata
    """
    from app.models.database import Document
    
    documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        DocumentMetadata(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            uploaded_at=doc.uploaded_at,
        )
        for doc in documents
    ]
