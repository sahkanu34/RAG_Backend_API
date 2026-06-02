"""Text chunking strategies."""
from abc import ABC, abstractmethod
from typing import List
import re


class TextChunker(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """Split text into chunks."""
        pass


class FixedSizeChunker(TextChunker):
    """Fixed-size chunking strategy with overlap."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize fixed-size chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            overlap: Number of overlapping characters between chunks
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        """Split text into fixed-size chunks with overlap."""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position accounting for overlap
            start = end - self.overlap
            
            # Ensure progress if at end of text
            if end == len(text):
                break
        
        return chunks


class SemanticChunker(TextChunker):
    """Semantic-based chunking strategy using sentence boundaries."""

    def __init__(self, target_size: int = 1000, overlap: int = 200):
        """Initialize semantic chunker.
        
        Args:
            target_size: Target size of chunks (respects sentence boundaries)
            overlap: Approximate overlap between chunks in characters
        """
        self.target_size = target_size
        self.overlap = overlap
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')

    def chunk(self, text: str) -> List[str]:
        """Split text into semantic chunks at sentence boundaries."""
        if not text.strip():
            return []
        
        # Split by sentences
        sentences = self.sentence_pattern.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return [text] if text.strip() else []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = f"{current_chunk} {sentence}".strip()
            
            if len(test_chunk) <= self.target_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Add overlap between chunks
        if len(chunks) > 1:
            chunks = self._add_overlap(chunks)
        
        return chunks

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between consecutive chunks."""
        if len(chunks) <= 1:
            return chunks
        
        overlapped = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]
            
            # Extract overlap from end of previous chunk
            overlap_start = max(0, len(prev_chunk) - self.overlap)
            overlap_text = prev_chunk[overlap_start:].strip()
            
            # Create overlapped chunk
            combined = f"{overlap_text} {curr_chunk}".strip()
            overlapped.append(combined)
        
        return overlapped


class ChunkerFactory:
    """Factory for creating text chunkers."""

    _chunkers = {
        "fixed": FixedSizeChunker,
        "semantic": SemanticChunker,
    }

    @classmethod
    def create(cls, strategy: str, **kwargs) -> TextChunker:
        """Create a chunker instance.
        
        Args:
            strategy: Chunking strategy ('fixed' or 'semantic')
            **kwargs: Arguments passed to the chunker
            
        Returns:
            TextChunker instance
        """
        chunker_class = cls._chunkers.get(strategy.lower())
        if not chunker_class:
            available = ", ".join(cls._chunkers.keys())
            raise ValueError(f"Unknown strategy: {strategy}. Available: {available}")
        
        return chunker_class(**kwargs)
