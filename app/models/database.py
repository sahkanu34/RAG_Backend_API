"""Database models for RAG backend."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Document(Base):
    """Document metadata stored in SQL database."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf or txt
    file_size = Column(Integer)
    original_text = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """Text chunks extracted from documents."""
    
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    chunking_strategy = Column(String(50), nullable=False)  # fixed or semantic
    embedding_id = Column(String(255))  # ID in vector database
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")


class Booking(Base):
    """Interview booking information."""
    
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(255), unique=True, nullable=False)
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=False)
    interview_date = Column(String(50), nullable=False)
    interview_time = Column(String(50), nullable=False)
    additional_info = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    extracted_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    """Chat session metadata."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(String(255), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String(255), nullable=True)
    session_metadata = Column(JSON)  # Additional metadata
