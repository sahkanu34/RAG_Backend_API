"""Pydantic schemas for API requests/responses."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# Document Ingestion API Schemas

class DocumentUploadResponse(BaseModel):
    """Response from document upload."""
    
    document_id: int
    filename: str
    file_type: str
    file_size: int
    chunks_created: int
    
    class Config:
        from_attributes = True


class DocumentMetadata(BaseModel):
    """Document metadata."""
    
    id: int
    filename: str
    file_type: str
    file_size: Optional[int]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# RAG Chat API Schemas

class ChatMessage(BaseModel):
    """Chat message in conversation."""
    
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    use_context: bool = True


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    
    session_id: str
    message: str
    role: str = "assistant"
    retrieved_chunks: int
    booking_extracted: bool
    booking_status: Optional[Dict[str, Any]] = None
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    """Response for chat history request."""
    
    session_id: str
    messages: List[ChatMessage]
    message_count: int
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: str
    message: str
    document_id: Optional[int] = None 

# Interview Booking Schemas

class BookingInfo(BaseModel):
    """Interview booking information."""
    
    name: str = Field(..., min_length=1)
    email: EmailStr
    interview_date: Optional[str] = None
    interview_time: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Response for booking request."""
    
    id: int
    session_id: str
    user_name: str
    user_email: str
    interview_date: Optional[str]
    interview_time: Optional[str]
    additional_info: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Error Response

class ErrorResponse(BaseModel):
    """Standard error response."""
    
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

from typing import Optional  # make sure this import exists at the top of schemas.py

class ChatRequest(BaseModel):
    session_id: str
    message: str
    document_id: Optional[int] = None   # NEW — add this line inside the existing class
 
