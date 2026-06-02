"""Document ingestion and processing service."""
import io
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.database import Document, Chunk
from app.services.chunking import TextChunker
from app.services.embeddings import EmbeddingsGenerator


class DocumentIngestor:
    """Service for ingesting and processing documents."""

    def __init__(
        self,
        db: Session,
        chunker: TextChunker,
        embeddings_generator: EmbeddingsGenerator,
        vector_db_client,
    ):
        """Initialize document ingestor.
        
        Args:
            db: Database session
            chunker: Text chunker instance
            embeddings_generator: Embeddings generator
            vector_db_client: Vector database client
        """
        self.db = db
        self.chunker = chunker
        self.embeddings_generator = embeddings_generator
        self.vector_db_client = vector_db_client

    def ingest_pdf(self, file_content: bytes, filename: str) -> Document:
        """Ingest PDF file.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            
        Returns:
            Document instance
        """
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber not installed")
        
        # Extract text from PDF
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
        
        return self._process_document(filename, "pdf", text, len(file_content))

    def ingest_text(self, file_content: bytes, filename: str) -> Document:
        """Ingest text file.
        
        Args:
            file_content: Text file bytes
            filename: Original filename
            
        Returns:
            Document instance
        """
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")
        
        return self._process_document(filename, "txt", text, len(file_content))

    def _process_document(
        self, filename: str, file_type: str, text: str, file_size: int
    ) -> Document:
        """Process document: chunk, embed, and store.
        
        Args:
            filename: Original filename
            file_type: File type (pdf or txt)
            text: Extracted text
            file_size: Original file size
            
        Returns:
            Stored Document instance
        """
        if not text.strip():
            raise ValueError("Document contains no text")
        
        # Ensure vector DB is connected
        if not self.vector_db_client.client:
            self.vector_db_client.connect()
            self.vector_db_client.create_collection()
        
        # Create document record
        doc = Document(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            original_text=text
        )
        self.db.add(doc)
        self.db.flush()  # Get the document ID
        
        # Chunk text
        chunks_text = self.chunker.chunk(text)
        if not chunks_text:
            raise ValueError("Document produced no chunks")
        
        # Generate embeddings
        embeddings = self.embeddings_generator.generate(chunks_text)
        
        # Store chunks and embeddings
        chunk_objects = []
        vector_ids = []
        metadata_list = []
        
        for idx, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
            chunk_id = f"doc_{doc.id}_chunk_{idx}"
            
            chunk_obj = Chunk(
                document_id=doc.id,
                chunk_index=idx,
                text=chunk_text,
                chunking_strategy=self.chunker.__class__.__name__,
                embedding_id=chunk_id
            )
            chunk_objects.append(chunk_obj)
            vector_ids.append(chunk_id)
            metadata_list.append({
                "document_id": doc.id,
                "filename": filename,
                "chunk_index": idx,
                "text": chunk_text
            })
        
        # Insert into SQL database
        self.db.add_all(chunk_objects)
        self.db.commit()
        
        # Insert into vector database
        self.vector_db_client.insert(
            vectors=embeddings,
            ids=vector_ids,
            metadata=metadata_list
        )
        
        return doc
