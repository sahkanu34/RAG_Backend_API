"""RAG system implementation."""
from typing import List, Tuple
import json

from app.services.vector_db import VectorDBClient, VectorSearchResult


class RAGSystem:
    """Custom RAG (Retrieval Augmented Generation) system."""

    def __init__(
        self,
        vector_db_client: VectorDBClient,
        llm_client,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ):
        """Initialize RAG system.
        
        Args:
            vector_db_client: Vector database client
            llm_client: LLM client with chat completion
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score
        """
        self.vector_db = vector_db_client
        self.llm_client = llm_client
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(self, query: str, query_embedding: List[float]) -> List[VectorSearchResult]:
        """Retrieve relevant documents.
        
        Args:
            query: User query text
            query_embedding: Query embedding vector
            
        Returns:
            List of relevant document chunks
        """
        results = self.vector_db.search(
            query_vector=query_embedding,
            top_k=self.top_k,
            threshold=self.similarity_threshold
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
            model="gpt-4",
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
    ) -> Tuple[str, List[VectorSearchResult]]:
        """Answer a user query using RAG.
        
        Args:
            query: User query
            query_embedding: Query embedding
            conversation_history: Previous messages for context
            
        Returns:
            Tuple of (response, retrieved_documents)
        """
        conversation_history = conversation_history or []
        
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, query_embedding)
        
        # Prepare context
        context = self.prepare_context(retrieved_docs)
        
        # Generate response
        response = self.generate_response(query, context, conversation_history)
        
        return response, retrieved_docs
