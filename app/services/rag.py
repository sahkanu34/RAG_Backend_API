"""RAG system implementation."""
from typing import List, Tuple, Optional, Dict, Any
import json
import logging

from app.services.vector_db import VectorDBClient, VectorSearchResult

logger = logging.getLogger(__name__)


class RAGSystem:
    """Custom RAG (Retrieval Augmented Generation) system."""

    def __init__(
        self,
        vector_db_client: VectorDBClient,
        llm_client,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        model: str = None,
    ):
        """Initialize RAG system.

        Args:
            vector_db_client: Vector database client
            llm_client: LLM client with chat completion (NvidiaChatClient)
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score
            model: Model name to use for generation. If not provided, falls
                back to llm_client.default_model (set from settings.NVIDIA_MODEL).
        """
        self.vector_db = vector_db_client
        self.llm_client = llm_client
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        # IMPORTANT: previously this was hardcoded to "gpt-4" in
        # generate_response(), which does not exist on the NVIDIA endpoint
        # and caused every generation call to fail, silently triggering the
        # generic fallback response in app/api/chat.py.
        self.model = model or getattr(llm_client, "default_model", None)
        if not self.model:
            raise ValueError(
                "RAGSystem requires a model name — pass model= explicitly "
                "or ensure llm_client.default_model is set."
            )

    def retrieve(
        self,
        query: str,
        query_embedding: List[float],
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Retrieve relevant documents.

        Args:
            query: User query text
            query_embedding: Query embedding vector
            filter_dict: Optional metadata filter, e.g. {"document_id": 5}

        Returns:
            List of relevant document chunks
        """
        results = self.vector_db.search(
            query_vector=query_embedding,
            top_k=self.top_k,
            threshold=self.similarity_threshold,
            filter_dict=filter_dict,
        )
        return results

    def prepare_context(self, retrieved_docs: List[VectorSearchResult]) -> str:
        """Prepare context from retrieved documents.

        Args:
            retrieved_docs: Retrieved document chunks

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No relevant documents found."

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(
                f"[Document {i}]\n{doc.text}\n"
            )

        return "\n".join(context_parts)

    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: List[dict],
    ) -> str:
        """Generate response using LLM.

        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous messages

        Returns:
            Generated response
        """
        system_prompt = """You are a helpful assistant that answers questions based on provided documents.
Use the document context to answer questions accurately. If the information is not in the documents, say so clearly.
Provide clear and concise answers."""

        messages = conversation_history.copy()

        messages.append({
            "role": "user",
            "content": f"""Answer the following question based on the provided documents.

DOCUMENTS:
{context}

QUESTION: {query}

Please provide a comprehensive answer based on the documents."""
        })

        response = self.llm_client.chat.completions.create(
            model=self.model,  # FIX: was hardcoded "gpt-4" — used the
                                # configured NVIDIA model instead.
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    def answer_query(
        self,
        query: str,
        query_embedding: List[float],
        conversation_history: List[dict] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[VectorSearchResult]]:
        """Answer a user query using RAG.

        Args:
            query: User query
            query_embedding: Query embedding
            conversation_history: Previous messages for context
            filter_dict: Optional metadata filter to scope retrieval,
                e.g. {"document_id": 5}

        Returns:
            Tuple of (response, retrieved_documents)
        """
        conversation_history = conversation_history or []

        # Retrieve relevant documents (scoped by filter_dict if provided)
        retrieved_docs = self.retrieve(query, query_embedding, filter_dict=filter_dict)

        # Prepare context
        context = self.prepare_context(retrieved_docs)

        try:
            # Generate response using LLM
            response = self.generate_response(query, context, conversation_history)
        except Exception as e:
            # If LLM fails, generate response from retrieved documents
            logger.warning("LLM generation failed, falling back to document-based response: %s", e)
            error_str = str(e)
            if any(keyword in error_str for keyword in ["timeout", "Read timed out", "ResourceExhausted", "503", "ConnectionPool"]):
                response = self._generate_document_based_response(query, context, retrieved_docs)
            else:
                raise

        return response, retrieved_docs

    def _generate_document_based_response(self, query: str, context: str, retrieved_docs: List[VectorSearchResult]) -> str:
        """Generate a response directly from retrieved documents when LLM is unavailable.

        Args:
            query: User query
            context: Formatted context from documents
            retrieved_docs: Retrieved document chunks

        Returns:
            Response synthesized from documents
        """
        # Build response from document snippets
        if not retrieved_docs:
            return f"I searched the documents for information about '{query}', but no relevant documents were found."

        # Use the most relevant document chunks directly
        response_parts = [f"Based on the documents, here's what I found about '{query}':\n"]

        for i, doc in enumerate(retrieved_docs[:3], 1):  # Use top 3 results
            # Add document excerpt with relevance score
            excerpt = doc.text[:500] if len(doc.text) > 500 else doc.text
            response_parts.append(f"\n**From Document {i}** (Relevance: {doc.score:.2f}):\n{excerpt}...\n")

        response_parts.append("\nThese excerpts from the documents provide the most relevant information for your query.")

        return "".join(response_parts)