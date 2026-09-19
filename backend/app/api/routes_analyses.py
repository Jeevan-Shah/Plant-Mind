"""Analysis retrieval endpoints (top-level, for history and detail views)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlantAnalysis
from ..services import plant_service

router = APIRouter(prefix='/api/analyses', tags=['analyses'])


@router.get('')
def list_all_analyses(plant_id: int | None = None, limit: int = 100,
                      db: Session = Depends(get_db)):
    """All stored analyses, newest first (optionally filtered by plant)."""
    stmt = select(PlantAnalysis).order_by(PlantAnalysis.created_at.desc()).limit(min(limit, 500))
    if plant_id is not None:
        stmt = stmt.where(PlantAnalysis.plant_id == plant_id)
    return [plant_service.serialize_analysis(a) for a in db.scalars(stmt)]


@router.get('/{analysis_id}')
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(PlantAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f'Analysis {analysis_id} not found')
    return plant_service.serialize_analysis(analysis)
