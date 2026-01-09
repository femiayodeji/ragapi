from typing import List
from datetime import datetime
import json
import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, SESSION_EXPIRE, SESSION_KEY_PREFIX


class Message:
    def __init__(self, role: str, content: str, timestamp: str = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["role"], data["content"], data.get("timestamp"))


class SessionService:
    def add_message(self, session_id: str, role: str, content: str):
        raise NotImplementedError
    
    def get_history(self, session_id: str, max_messages: int = None) -> List[Message]:
        raise NotImplementedError
    
    def clear_session(self, session_id: str):
        raise NotImplementedError
    
    def session_exists(self, session_id: str) -> bool:
        raise NotImplementedError
    
    def format_history(self, session_id: str, max_messages: int = None) -> str:
        history = self.get_history(session_id, max_messages)
        if not history:
            return ""
        return "\n".join([
            f"{'Human' if msg.role == 'user' else 'Assistant'}: {msg.content}"
            for msg in history
        ])


class RedisSessionService(SessionService):
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        try:
            self.client.ping()
            print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as error:
            print(f"Failed to connect to Redis: {error}")
            raise
    
    def add_message(self, session_id: str, role: str, content: str):
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        message = Message(role, content)
        self.client.rpush(key, json.dumps(message.to_dict()))
        if SESSION_EXPIRE > 0:
            self.client.expire(key, SESSION_EXPIRE)
    
    def get_history(self, session_id: str, max_messages: int = None) -> List[Message]:
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        messages_data = self.client.lrange(key, -max_messages if max_messages else 0, -1)
        return [Message.from_dict(json.loads(msg_json)) for msg_json in messages_data]
    
    def clear_session(self, session_id: str):
        self.client.delete(f"{SESSION_KEY_PREFIX}{session_id}")
    
    def session_exists(self, session_id: str) -> bool:
        return self.client.exists(f"{SESSION_KEY_PREFIX}{session_id}") > 0


class InMemorySessionService(SessionService):
    def __init__(self):
        self.sessions = {}
    
    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(Message(role, content))
    
    def get_history(self, session_id: str, max_messages: int = None) -> List[Message]:
        if session_id not in self.sessions:
            return []
        messages = self.sessions[session_id]
        return messages[-max_messages:] if max_messages else messages
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def session_exists(self, session_id: str) -> bool:
        return session_id in self.sessions


def get_session_service(backend: str = "redis"):
    if backend.lower() == "redis":
        try:
            return RedisSessionService()
        except Exception:
            return InMemorySessionService()
    return InMemorySessionService()
