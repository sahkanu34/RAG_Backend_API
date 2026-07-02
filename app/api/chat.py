"""Conversational RAG API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.schemas import ChatRequest, ChatResponse, ChatHistoryResponse, BookingResponse
from app.services.chat_memory import ChatMemoryManager
from app.services.rag import RAGSystem
from app.services.booking import BookingExtractor
from app.services.embeddings import get_embeddings_generator
from app.services.nvidia_client import NvidiaChatClient
from app.services.vector_db import get_vector_db_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize services (could be moved to dependency injection)
_chat_memory: ChatMemoryManager = None
_embeddings_gen = None
_vector_db = None
_rag_system: RAGSystem = None
_booking_extractor: BookingExtractor = None


def _init_services():
    """Initialize chat services."""
    global _chat_memory, _embeddings_gen, _vector_db, _rag_system, _booking_extractor

    if _chat_memory is None:
        try:
            _chat_memory = ChatMemoryManager(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                ttl=settings.REDIS_CHAT_EXPIRY,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Redis connection failed: {str(e)}"
            )

    if _embeddings_gen is None:
        _embeddings_gen = get_embeddings_generator(
            api_key=settings.NVIDIA_API_KEY,
            model=settings.NVIDIA_EMBEDDING_MODEL,
        )

    if _vector_db is None:
        try:
            _vector_db = get_vector_db_client(
                db_type=settings.VECTOR_DB_TYPE,
                url=settings.QDRANT_URL if settings.VECTOR_DB_TYPE == "qdrant" else None,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vector_size=getattr(_embeddings_gen, "dimension", settings.EMBEDDING_VECTOR_SIZE),
            )
            _vector_db.connect()
            _vector_db.create_collection()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Vector database connection failed: {str(e)}"
            )

    if _rag_system is None:
        try:
            llm_client = NvidiaChatClient(
                api_key=settings.NVIDIA_API_KEY,
                default_model=settings.NVIDIA_MODEL,
            )
            _rag_system = RAGSystem(
                vector_db_client=_vector_db,
                llm_client=llm_client,
                top_k=settings.TOP_K_RETRIEVAL,
                similarity_threshold=settings.SIMILARITY_THRESHOLD,
                # FIX: explicitly wire the configured NVIDIA model through,
                # so RAGSystem never falls back to a hardcoded "gpt-4".
                model=settings.NVIDIA_MODEL,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"RAG system initialization failed: {str(e)}"
            )


@router.post("/start", response_model=dict)
async def start_session() -> dict:
    """Start a new chat session.

    Returns:
        Dictionary with session_id
    """
    _init_services()

    try:
        session_id = _chat_memory.create_session()
        return {
            "session_id": session_id,
            "message": "Chat session started"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a message and get RAG response.

    Handles multi-turn conversation, retrieves relevant documents,
    generates response, and extracts booking intent if present.

    Args:
        request: ChatRequest with session_id, message, and optional document_id
        db: Database session

    Returns:
        ChatResponse with assistant message and metadata
    """
    _init_services()

    try:
        # Validate session
        if not _chat_memory.session_exists(request.session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Store user message
        _chat_memory.add_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )

        # Generate query embedding
        query_embeddings = _embeddings_gen.generate([request.message])
        if not query_embeddings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding"
            )

        # Get conversation history for context
        history = _chat_memory.get_history(request.session_id, limit=10)
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        # Scope retrieval to a specific document if one was provided.
        # Without this, retrieval searches across every document ever
        # uploaded, which causes answers to bleed in from unrelated docs.
        filter_dict = {"document_id": request.document_id} if request.document_id else None

        # Generate RAG response
        response, retrieved_docs = _rag_system.answer_query(
            query=request.message,
            query_embedding=query_embeddings[0],
            conversation_history=history_dicts,
            filter_dict=filter_dict,
        )

        # Store assistant response
        _chat_memory.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response
        )

        # Extract booking intent
        booking_extracted = False
        booking_status = None

        try:
            booking_extractor = BookingExtractor(
                llm_client=_rag_system.llm_client,
                db=db
            )

            history_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in _chat_memory.get_history(request.session_id)
            ]

            booking_data = booking_extractor.extract_booking_intent(
                conversation_history=history_dicts,
                session_id=request.session_id
            )

            if booking_data:
                booking = booking_extractor.save_booking(
                    session_id=request.session_id,
                    booking_data=booking_data
                )
                booking_extracted = True
                booking_status = {
                    "id": booking.id,
                    "name": booking.user_name,
                    "email": booking.user_email,
                    "date": booking.interview_date,
                    "time": booking.interview_time,
                }
        except Exception as e:
            # Log but don't fail on booking extraction error
            logger.warning("Booking extraction failed for session %s: %s", request.session_id, e)

        from datetime import datetime
        return ChatResponse(
            session_id=request.session_id,
            message=response,
            role="assistant",
            retrieved_chunks=len(retrieved_docs),
            booking_extracted=booking_extracted,
            booking_status=booking_status,
            timestamp=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        # Log the real error so failures are visible instead of silently
        # masked by a generic user-facing message.
        logger.error(
            "Chat processing error for session %s (query=%r): %s",
            request.session_id, request.message, error_str, exc_info=True,
        )

        # Handle timeouts / connection errors by degrading gracefully using
        # the documents we already retrieved (if any), instead of returning
        # a hardcoded, context-free string. This mirrors RAGSystem's own
        # _generate_document_based_response so the user still gets a real
        # answer whenever retrieval succeeded even though generation failed.
        if any(keyword in error_str for keyword in ["timeout", "Read timed out", "ConnectionPool", "ResourceExhausted", "503"]):
            try:
                query_embeddings = _embeddings_gen.generate([request.message])
                filter_dict = {"document_id": request.document_id} if request.document_id else None
                retrieved_docs = _rag_system.retrieve(
                    query=request.message,
                    query_embedding=query_embeddings[0] if query_embeddings else [],
                    filter_dict=filter_dict,
                )
                context = _rag_system.prepare_context(retrieved_docs)
                simple_response = _rag_system._generate_document_based_response(
                    request.message, context, retrieved_docs
                )

                _chat_memory.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=simple_response
                )

                from datetime import datetime
                return ChatResponse(
                    session_id=request.session_id,
                    message=simple_response,
                    role="assistant",
                    retrieved_chunks=len(retrieved_docs),
                    booking_extracted=False,
                    booking_status=None,
                    timestamp=datetime.utcnow(),
                )
            except Exception as fallback_error:
                logger.error("Fallback response generation also failed: %s", fallback_error, exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"LLM service temporarily unavailable: {str(e)}"
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str) -> ChatHistoryResponse:
    """Get chat history for a session.

    Args:
        session_id: Chat session ID

    Returns:
        ChatHistoryResponse with all messages
    """
    _init_services()

    try:
        if not _chat_memory.session_exists(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        from app.schemas.schemas import ChatMessage as ChatMessageSchema
        from datetime import datetime

        history = _chat_memory.get_history(session_id)
        session_info = _chat_memory.get_session_info(session_id)

        messages = [
            ChatMessageSchema(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
            )
            for msg in history
        ]

        created_at = datetime.fromisoformat(session_info["created_at"]) if session_info else datetime.utcnow()

        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            message_count=len(messages),
            created_at=created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a chat session.

    Args:
        session_id: Chat session ID

    Returns:
        Confirmation message
    """
    _init_services()

    try:
        if not _chat_memory.session_exists(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        _chat_memory.clear_session(session_id)

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )