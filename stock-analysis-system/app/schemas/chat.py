"""
Chat Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., description="User input message")
    session_id: str = Field(..., description="Session ID")
    subject_user_id: Optional[int] = Field(None, description="Advisor mode: target client user id")


class ChatMessageResponse(BaseModel):
    """Chat message response"""
    role: str = Field(..., description="Message role: user/assistant")
    content: str = Field(..., description="Message content")
    function_name: Optional[str] = Field(None, description="Called function name")
    function_args: Optional[Dict[str, Any]] = Field(None, description="Function arguments")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation time")
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Session response"""
    session_id: str
    message_count: int
    last_message_at: Optional[datetime]
    first_message_at: Optional[datetime]


class ChatHistoryResponse(BaseModel):
    """Session history response"""
    session_id: str
    messages: List[ChatMessageResponse]
    
    class Config:
        from_attributes = True


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    content: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    done: bool = False
    error: Optional[str] = None


