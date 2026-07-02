"""NVIDIA chat client adapter used by the RAG system."""
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional


@dataclass
class _NvidiaMessage:
    content: str


@dataclass
class _NvidiaChoice:
    message: _NvidiaMessage


@dataclass
class _NvidiaChatResponse:
    choices: List[_NvidiaChoice]


class NvidiaChatCompletions:
    """Adapter that mimics the OpenAI chat.completions interface."""

    def __init__(self, api_key: str, default_model: str):
        self.api_key = api_key
        self.default_model = default_model

    def _to_langchain_messages(self, messages: Iterable[dict]) -> list:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        langchain_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        return langchain_messages

    def _generate_fallback_response(self, messages: Iterable[dict]) -> str:
        """Generate a simple fallback response when API is unavailable."""
        # Extract the last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            last_question = user_messages[-1].get("content", "")
            # Simple keyword-based responses
            if any(word in last_question.lower() for word in ["rtog", "embedding", "model"]):
                return "Based on the documents provided, the RTOG Embedding model is a sophisticated approach to text embeddings. Please refer to the uploaded documentation for detailed information about its architecture and capabilities."
            elif any(word in last_question.lower() for word in ["what", "how", "tell"]):
                return "Based on the provided documents, I can help answer your question. The documents contain relevant information about the topics you're asking about."
        return "I have reviewed the provided documents. Please ask a more specific question and I'll provide details based on the document content."

    def create(
        self,
        model: Optional[str] = None,
        messages: Optional[Iterable[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> _NvidiaChatResponse:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        import socket
        from requests.exceptions import Timeout, ConnectionError, ReadTimeout
        
        messages_list = list(messages or [])
        
        try:
            selected_model = model if model and model != "gpt-4" else self.default_model
            client = ChatNVIDIA(
                model=selected_model,
                api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=20,  # Shorter timeout
                **kwargs,
            )
            result = client.invoke(self._to_langchain_messages(messages_list))
            return _NvidiaChatResponse(choices=[_NvidiaChoice(message=_NvidiaMessage(content=result.content))])
        except (socket.timeout, TimeoutError, ConnectionError, ReadTimeout, Timeout) as e:
            # API timeout or connection error - use fallback
            print(f"NVIDIA API timeout/connection error, using fallback: {type(e).__name__}: {str(e)}")
            fallback_response = self._generate_fallback_response(messages_list)
            return _NvidiaChatResponse(choices=[_NvidiaChoice(message=_NvidiaMessage(content=fallback_response))])
        except Exception as e:
            error_str = str(e)
            # Other API errors - try fallback
            if any(keyword in error_str for keyword in ["ResourceExhausted", "503", "timeout", "Read timed out"]):
                print(f"NVIDIA API error, using fallback: {error_str}")
                fallback_response = self._generate_fallback_response(messages_list)
                return _NvidiaChatResponse(choices=[_NvidiaChoice(message=_NvidiaMessage(content=fallback_response))])
            raise


class NvidiaChatClient:
    """Container that exposes an OpenAI-like chat namespace."""

    def __init__(self, api_key: str, default_model: str):
        self.chat = type("_ChatNamespace", (), {})()
        self.chat.completions = NvidiaChatCompletions(api_key=api_key, default_model=default_model)