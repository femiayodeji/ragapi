from pydantic import BaseModel, field_validator
from typing import Optional


MAX_QUESTION_LENGTH = 5000


class Query(BaseModel):
    question: str
    session_id: Optional[str] = None
    
    @field_validator('question')
    @classmethod
    def question_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError('Question cannot be empty')
        if len(value) > MAX_QUESTION_LENGTH:
            raise ValueError(f'Question too long (max {MAX_QUESTION_LENGTH} characters)')
        return value.strip()
