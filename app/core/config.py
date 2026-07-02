"""Configuration module for RAG backend."""
import os
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # LLM Settings
    LLM_PROVIDER: Literal["nvidia"] = "nvidia"
    NVIDIA_API_KEY: str = os.getenv(
        "NVIDIA_API_KEY",
        "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",
    )
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_EMBEDDING_MODEL: str = "NV-Embed-QA"
    EMBEDDING_VECTOR_SIZE: int = 1024

    # Vector DB Settings
    VECTOR_DB_TYPE: Literal["pinecone", "qdrant", "weaviate", "milvus"] = "qdrant"
    
    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "documents_nvidia"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "documents_nvidia"
    
    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_CLASS_NAME: str = "Document"
    
    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "documents"

    # SQL Database
    DATABASE_URL: str = "sqlite:///./rag_backend.db"
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CHAT_EXPIRY: int = 86400  # 24 hours

    # Chunking Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    CHUNKING_STRATEGY: Literal["fixed", "semantic"] = "fixed"

    # RAG Settings
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_THRESHOLD: float = 0.3
    USE_RERANKING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
