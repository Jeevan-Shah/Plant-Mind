"""Follow-up chat endpoint - doubts after an analysis result."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlantAnalysis
from ..schemas import ChatRequest, ChatResponse
from ..services import chat_service

router = APIRouter(prefix='/api', tags=['chat'])


@router.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Answer the user's latest question about an existing analysis.

    Stateless: the client sends the whole conversation; only the final user
    turn is answered, grounded in the stored analysis plus question-focused
    knowledge-graph retrieval (LLM when configured, deterministic fallback
    otherwise).
    """
    analysis = db.get(PlantAnalysis, payload.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404,
                            detail=f'Analysis {payload.analysis_id} not found')
    if payload.messages[-1].role != 'user':
        raise HTTPException(status_code=400,
                            detail='The last message must be from the user')
    return chat_service.answer(db, analysis,
                               [m.model_dump() for m in payload.messages])