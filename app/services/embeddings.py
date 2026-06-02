"""Embeddings generation service."""
from abc import ABC, abstractmethod
from typing import List


class EmbeddingsGenerator(ABC):
    """Abstract base class for embeddings generation."""

    @abstractmethod
    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass


class OpenAIEmbeddings(EmbeddingsGenerator):
    """Generate embeddings using OpenAI API."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialize OpenAI embeddings.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        self.api_key = api_key
        self.model = model
        self.client = None

    def _init_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai not installed")

    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        if not self.client:
            self._init_client()
        
        if not texts:
            return []
        
        # Remove empty strings
        texts = [t.strip() for t in texts if t.strip()]
        if not texts:
            return []
        
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        
        # Sort by index to maintain order
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in embeddings]


def get_embeddings_generator(api_key: str, model: str = "text-embedding-3-small") -> EmbeddingsGenerator:
    """Factory function to get embeddings generator.
    
    Args:
        api_key: API key for the provider
        model: Model name
        
    Returns:
        EmbeddingsGenerator instance
    """
    return OpenAIEmbeddings(api_key=api_key, model=model)
