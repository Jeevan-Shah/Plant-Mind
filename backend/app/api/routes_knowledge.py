"""Knowledge graph exploration endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import EntityOut, RelationshipSetOut
from ..services import knowledge_service

router = APIRouter(prefix='/api/knowledge', tags=['knowledge'])


@router.get('/search', response_model=list[EntityOut])
def search(q: str | None = None, entity_type: str | None = None,
           db: Session = Depends(get_db)):
    return knowledge_service.list_entities(db, entity_type=entity_type, q=q)


@router.get('/types')
def types(db: Session = Depends(get_db)):
    """Entity types with counts, for the Knowledge Explorer tabs."""
    entities = knowledge_service.list_entities(db, limit=1000)
    counts: dict[str, int] = {}
    for e in entities:
        counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
    return counts


@router.get('/entity/{entity_id}', response_model=EntityOut)
def entity(entity_id: str, db: Session = Depends(get_db)):
    e = knowledge_service.get_entity(db, entity_id)
    if not e:
        raise HTTPException(status_code=404, detail=f'Entity "{entity_id}" not found')
    return e


@router.get('/relationships/{entity_id}', response_model=RelationshipSetOut)
def relationships(entity_id: str, db: Session = Depends(get_db)):
    result = knowledge_service.get_relationships(db, entity_id)
    if not result['entity']:
        raise HTTPException(status_code=404, detail=f'Entity "{entity_id}" not found')
    return result
