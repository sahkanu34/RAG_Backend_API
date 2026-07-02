"""Embeddings generation service."""
import hashlib
from abc import ABC, abstractmethod
from typing import List


class EmbeddingsGenerator(ABC):
    """Abstract base class for embeddings generation."""

    dimension: int = 0

    @abstractmethod
    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass


class FallbackEmbeddingsGenerator(EmbeddingsGenerator):
    """Fallback embeddings generator using hash-based vectors."""

    dimension = 1024

    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings using hash."""
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            if not text.strip():
                # Return zero vector for empty text
                embeddings.append([0.0] * self.dimension)
                continue
            
            # Create deterministic embedding from text hash
            h = hashlib.sha256(text.encode()).digest()
            # Convert hash bytes to floats in range [-1, 1]
            embedding = [(int.from_bytes(h[i*2:i*2+2], 'little') / 32768.0) - 1.0 
                        for i in range(self.dimension)]
            embeddings.append(embedding)
        
        return embeddings


class NvidiaEmbeddingsGenerator(EmbeddingsGenerator):
    """Generate embeddings using NVIDIA AI Endpoints with fallback."""

    dimension = 1024

    def __init__(self, api_key: str, model: str = "NV-Embed-QA"):
        """Initialize NVIDIA embeddings.
        
        Args:
            api_key: NVIDIA API key
            model: Embedding model name
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        self.fallback = None
        self._init_attempted = False

    def _init_client(self) -> None:
        """Initialize NVIDIA client with fallback."""
        if self._init_attempted:
            return
        
        self._init_attempted = True
        try:
            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

            self.client = NVIDIAEmbeddings(
                model=self.model,
                api_key=self.api_key,
                truncate="END",
            )
        except Exception as e:
            print(f"Warning: NVIDIA embeddings initialization failed: {e}")
            print("Falling back to hash-based embeddings for document processing")
            self.fallback = FallbackEmbeddingsGenerator()

    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using NVIDIA or fallback."""
        if not self.client and not self.fallback:
            self._init_client()
        
        if not texts:
            return []
        
        # Remove empty strings
        texts = [t.strip() for t in texts if t.strip()]
        if not texts:
            return []
        
        # Try NVIDIA first
        if self.client:
            try:
                return self.client.embed_documents(texts)
            except Exception as e:
                print(f"Warning: NVIDIA embedding failed: {e}")
                print("Falling back to hash-based embeddings")
                self.fallback = FallbackEmbeddingsGenerator()
        
        # Use fallback
        if self.fallback:
            return self.fallback.generate(texts)
        
        return []


def get_embeddings_generator(api_key: str, model: str = "NV-Embed-QA") -> EmbeddingsGenerator:
    """Factory function to get embeddings generator.
    
    Args:
        api_key: API key for the provider
        model: Model name
        
    Returns:
        EmbeddingsGenerator instance
    """
    return NvidiaEmbeddingsGenerator(api_key=api_key, model=model)
