"""Vector database client abstraction layer."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Result from vector search."""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class VectorDBClient(ABC):
    """Abstract base class for vector database clients."""

    @abstractmethod
    def connect(self) -> None:
        """Initialize connection to vector database."""
        pass

    @abstractmethod
    def create_collection(self) -> None:
        """Create collection/index."""
        pass

    @abstractmethod
    def insert(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        """Insert vectors with metadata."""
        pass

    @abstractmethod
    def search(
        self, query_vector: List[float], top_k: int = 5, threshold: float = 0.3
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connection."""
        pass


class QdrantClient(VectorDBClient):
    """Qdrant vector database client."""

    def __init__(self, url: str, collection_name: str, vector_size: int = 1536):
        """Initialize Qdrant client.
        
        Args:
            url: Qdrant server URL
            collection_name: Name of the collection
            vector_size: Dimension of vectors (default for text-embedding-3-small)
        """
        self.url = url
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = None

    def connect(self) -> None:
        """Initialize Qdrant client."""
        try:
            from qdrant_client import QdrantClient as QdrantLib
            from qdrant_client.http.models import Distance, VectorParams
            
            self.client = QdrantLib(url=self.url)
            self.Distance = Distance
            self.VectorParams = VectorParams
        except ImportError:
            raise ImportError("qdrant-client not installed")

    def create_collection(self) -> None:
        """Create collection if not exists."""
        if not self.client:
            self.connect()
        
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=self.VectorParams(
                    size=self.vector_size,
                    distance=self.Distance.COSINE
                ),
            )

    def insert(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        """Insert vectors with metadata."""
        if not self.client:
            self.connect()
        
        from qdrant_client.http.models import PointStruct
        
        points = [
            PointStruct(
                id=int(hash(id_) & 0x7fffffff),
                vector=vector,
                payload={"id": id_, "text": meta.get("text", ""), "metadata": meta}
            )
            for id_, vector, meta in zip(ids, vectors, metadata)
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self, query_vector: List[float], top_k: int = 5, threshold: float = 0.3
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        if not self.client:
            self.connect()
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=threshold,
        )
        
        search_results = []
        for result in results:
            payload = result.payload
            search_results.append(
                VectorSearchResult(
                    id=payload.get("id", ""),
                    text=payload.get("text", ""),
                    score=result.score,
                    metadata=payload.get("metadata", {})
                )
            )
        return search_results

    def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs."""
        if not self.client:
            self.connect()
        
        numeric_ids = [int(hash(id_) & 0x7fffffff) for id_ in ids]
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=numeric_ids,
        )

    def close(self) -> None:
        """Close client connection."""
        if self.client:
            self.client.close()


class PineconeClient(VectorDBClient):
    """Pinecone vector database client."""

    def __init__(self, api_key: str, environment: str, index_name: str, vector_size: int = 1536):
        """Initialize Pinecone client."""
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.vector_size = vector_size
        self.client = None
        self.index = None

    def connect(self) -> None:
        """Initialize Pinecone connection."""
        try:
            from pinecone import Pinecone
            
            self.client = Pinecone(api_key=self.api_key)
            self.index = self.client.Index(self.index_name)
        except ImportError:
            raise ImportError("pinecone-client not installed")

    def create_collection(self) -> None:
        """Create index if not exists."""
        if not self.client:
            self.connect()
        
        # Pinecone index creation typically done via console
        # This is a no-op for compatibility

    def insert(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        """Insert vectors with metadata."""
        if not self.index:
            self.connect()
        
        vectors_to_upsert = [
            (id_, vector, meta)
            for id_, vector, meta in zip(ids, vectors, metadata)
        ]
        self.index.upsert(vectors=vectors_to_upsert)

    def search(
        self, query_vector: List[float], top_k: int = 5, threshold: float = 0.3
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        if not self.index:
            self.connect()
        
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )
        
        search_results = []
        for match in results.get("matches", []):
            if match["score"] >= threshold:
                metadata = match.get("metadata", {})
                search_results.append(
                    VectorSearchResult(
                        id=match["id"],
                        text=metadata.get("text", ""),
                        score=match["score"],
                        metadata=metadata
                    )
                )
        return search_results

    def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs."""
        if not self.index:
            self.connect()
        
        self.index.delete(ids=ids)

    def close(self) -> None:
        """Close connection."""
        pass


def get_vector_db_client(db_type: str, **kwargs) -> VectorDBClient:
    """Factory function to get appropriate vector database client.
    
    Args:
        db_type: Type of vector database (qdrant, pinecone, weaviate, milvus)
        **kwargs: Additional arguments for the client
        
    Returns:
        VectorDBClient instance (not yet connected)
    """
    if db_type.lower() == "qdrant":
        client = QdrantClient(
            url=kwargs.get("url", "http://localhost:6333"),
            collection_name=kwargs.get("collection_name", "documents"),
            vector_size=kwargs.get("vector_size", 1536)
        )
    elif db_type.lower() == "pinecone":
        client = PineconeClient(
            api_key=kwargs.get("api_key", ""),
            environment=kwargs.get("environment", ""),
            index_name=kwargs.get("index_name", "documents"),
            vector_size=kwargs.get("vector_size", 1536)
        )
    else:
        raise ValueError(f"Unsupported vector database type: {db_type}")
    
    # Defer connection to first use
    return client
