"""Chat memory management using Redis."""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import redis


class ChatMessage:
    """Represents a chat message."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize chat message.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            timestamp: Message timestamp
            metadata: Additional metadata
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data["timestamp"])
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            metadata=data.get("metadata", {})
        )


class ChatMemoryManager:
    """Manages chat conversation history in Redis."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 86400,  # 24 hours
    ):
        """Initialize chat memory manager.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            ttl: Time to live for session in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ttl = ttl
        self.redis_client = None
        self._connected = False

    def _ensure_connected(self) -> None:
        """Ensure Redis is connected."""
        if self._connected:
            return
        
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self.redis_client.ping()
            self._connected = True
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new chat session.
        
        Args:
            user_id: Optional user ID for the session
            
        Returns:
            Session ID
        """
        self._ensure_connected()
        session_id = str(uuid.uuid4())
        session_key = f"chat_session:{session_id}"
        
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "user_id": user_id or "",
            "message_count": "0"
        }
        
        self.redis_client.hset(session_key, mapping=session_data)
        self.redis_client.expire(session_key, self.ttl)
        
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add message to session history.
        
        Args:
            session_id: Session ID
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata
        """
        self._ensure_connected()
        message = ChatMessage(role=role, content=content, metadata=metadata)
        
        session_key = f"chat_session:{session_id}"
        messages_key = f"chat_messages:{session_id}"
        
        # Store message
        self.redis_client.lpush(messages_key, json.dumps(message.to_dict()))
        
        # Update message count
        count = self.redis_client.hget(session_key, "message_count")
        new_count = int(count or 0) + 1
        self.redis_client.hset(session_key, "message_count", str(new_count))
        
        # Reset TTL
        self.redis_client.expire(session_key, self.ttl)
        self.redis_client.expire(messages_key, self.ttl)

    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get chat history for a session.
        
        Args:
            session_id: Session ID
            limit: Limit number of messages (from most recent)
            
        Returns:
            List of ChatMessage objects
        """
        self._ensure_connected()
        messages_key = f"chat_messages:{session_id}"
        
        # Redis stores most recent first (lpush)
        if limit:
            messages = self.redis_client.lrange(messages_key, 0, limit - 1)
        else:
            messages = self.redis_client.lrange(messages_key, 0, -1)
        
        # Reverse to get chronological order
        chat_messages = [
            ChatMessage.from_dict(json.loads(msg))
            for msg in reversed(messages)
        ]
        
        return chat_messages

    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session.
        
        Args:
            session_id: Session ID
        """
        self._ensure_connected()
        session_key = f"chat_session:{session_id}"
        messages_key = f"chat_messages:{session_id}"
        
        self.redis_client.delete(session_key)
        self.redis_client.delete(messages_key)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session exists
        """
        self._ensure_connected()
        session_key = f"chat_session:{session_id}"
        return self.redis_client.exists(session_key) > 0

    def get_session_info(self, session_id: str) -> Optional[Dict[str, str]]:
        """Get session metadata.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session metadata or None
        """
        self._ensure_connected()
        session_key = f"chat_session:{session_id}"
        info = self.redis_client.hgetall(session_key)
        return info if info else None
