"""
Chat API Endpoints
API endpoints for the AI analysis assistant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import logging
from datetime import datetime
import uuid

from app.database import get_db
from app.models.user import User, UserRole
from app.models.chat_message import ChatMessage as ChatMessageModel, MessageRole
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatHistoryResponse
)
from app.services.ai.langchain_service import get_chat_service
from app.services.auth_service import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Chat"])  # prefix is set to /chat in main.py


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send message to AI (non-streaming)
    """
    try:
        chat_service = get_chat_service()
        
        # Determine target user id (advisor can specify a client)
        target_user_id = current_user.id
        if getattr(current_user, "role", None) == UserRole.ADVISOR and getattr(request, "subject_user_id", None):
            target_user_id = int(request.subject_user_id)

        # Save user message
        user_message = ChatMessageModel(
            user_id=current_user.id,
            session_id=request.session_id,
            role=MessageRole.USER,
            content=request.message,
            extra_data={"subject_user_id": target_user_id} if target_user_id != current_user.id else None,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        # Call LangChain Agent
        result = await chat_service.chat(
            user_input=request.message,
            session_id=request.session_id,
            user_id=target_user_id
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error")
            )
        
        # Save AI response
        ai_message = ChatMessageModel(
            user_id=current_user.id,
            session_id=request.session_id,
            role=MessageRole.ASSISTANT,
            content=result["response"],
            extra_data={"intermediate_steps": result.get("intermediate_steps", []), "subject_user_id": target_user_id},
            created_at=datetime.utcnow()
        )
        db.add(ai_message)
        db.commit()
        
        return ChatMessageResponse(
            role="assistant",
            content=result["response"],
            function_name=None,
            function_args=None,
            metadata={"intermediate_steps": result.get("intermediate_steps", [])},
            created_at=ai_message.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/stream")
async def stream_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send message to AI (streaming response - Server-Sent Events)
    """
    try:
        chat_service = get_chat_service()
        
        # Save user message
        user_message = ChatMessageModel(
            user_id=current_user.id,
            session_id=request.session_id,
            role=MessageRole.USER,
            content=request.message,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        # Determine target user id
        target_user_id = current_user.id
        if getattr(current_user, "role", None) == UserRole.ADVISOR and getattr(request, "subject_user_id", None):
            target_user_id = int(request.subject_user_id)

        # Streaming response generator
        async def event_generator():
            full_response = ""
            try:
                # Send start signal
                yield f"data: {json.dumps({'type': 'start', 'content': ''})}\n\n"
                
                # Stream response
                async for chunk in chat_service.chat_stream(
                    user_input=request.message,
                    session_id=request.session_id,
                    user_id=target_user_id
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Save full AI response to DB
                ai_message = ChatMessageModel(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    extra_data={"subject_user_id": target_user_id},
                    created_at=datetime.utcnow()
                )
                db.add(ai_message)
                db.commit()
                
                # Send done signal
                yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Stream message error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream message: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all sessions for the current user
    """
    try:
        # Query all sessions for user
        sessions = db.query(
            ChatMessageModel.session_id,
            db.func.count(ChatMessageModel.id).label("message_count"),
            db.func.max(ChatMessageModel.created_at).label("last_message_at"),
            db.func.min(ChatMessageModel.created_at).label("first_message_at")
        ).filter(
            ChatMessageModel.user_id == current_user.id
        ).group_by(
            ChatMessageModel.session_id
        ).order_by(
            db.func.max(ChatMessageModel.created_at).desc()
        ).all()
        
        return [
            ChatSessionResponse(
                session_id=s.session_id,
                message_count=s.message_count,
                last_message_at=s.last_message_at,
                first_message_at=s.first_message_at
            )
            for s in sessions
        ]
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sessions"
        )


@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get historical messages for a given session
    """
    try:
        messages = db.query(ChatMessageModel).filter(
            ChatMessageModel.user_id == current_user.id,
            ChatMessageModel.session_id == session_id
        ).order_by(
            ChatMessageModel.created_at.asc()
        ).all()
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=[
                ChatMessageResponse(
                    role=msg.role.value,
                    content=msg.content,
                    function_name=msg.function_name,
                    function_args=msg.function_args,
                    metadata=msg.extra_data,
                    created_at=msg.created_at
                )
                for msg in messages
            ]
        )
        
    except Exception as e:
        logger.error(f"Get session history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session history"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific session
    """
    try:
        # Delete DB messages
        db.query(ChatMessageModel).filter(
            ChatMessageModel.user_id == current_user.id,
            ChatMessageModel.session_id == session_id
        ).delete()
        db.commit()
        
        # Clear in-memory session history
        chat_service = get_chat_service()
        chat_service.clear_session(session_id)
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete session error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.post("/sessions/new")
async def create_new_session(
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new session (returns new session_id)
    """
    session_id = f"session_{uuid.uuid4().hex[:16]}"
    return {"session_id": session_id}

