"""Plant CRUD, analysis and care-history endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Plant, PlantAnalysis, CareEvent
from ..schemas import AnalysisRequest, CareInput, CareOut, PlantInput, PlantOut
from ..services import analysis_service, plant_service

router = APIRouter(prefix='/api/plants', tags=['plants'])


def _get_plant_or_404(db: Session, plant_id: int) -> Plant:
    plant = db.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail=f'Plant {plant_id} not found')
    return plant


@router.post('', response_model=PlantOut, status_code=201)
def create_plant(payload: PlantInput, db: Session = Depends(get_db)):
    plant = Plant(**payload.model_dump())
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant_service.serialize_plant(db, plant)


@router.get('', response_model=list[PlantOut])
def list_plants(db: Session = Depends(get_db)):
    plants = list(db.scalars(select(Plant).order_by(Plant.created_at.desc())))
    return [plant_service.serialize_plant(db, p) for p in plants]


@router.get('/{plant_id}', response_model=PlantOut)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    return plant_service.serialize_plant(db, _get_plant_or_404(db, plant_id))


@router.put('/{plant_id}', response_model=PlantOut)
def update_plant(plant_id: int, payload: PlantInput, db: Session = Depends(get_db)):
    plant = _get_plant_or_404(db, plant_id)
    for key, value in payload.model_dump().items():
        setattr(plant, key, value)
    db.commit()
    db.refresh(plant)
    return plant_service.serialize_plant(db, plant)


@router.delete('/{plant_id}', status_code=204)
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = _get_plant_or_404(db, plant_id)
    db.delete(plant)
    db.commit()


@router.post('/{plant_id}/analyze')
async def analyze_plant(plant_id: int,
                        image: UploadFile = File(...),
                        symptoms: str | None = Form(default=None),
                        db: Session = Depends(get_db)):
    """Run the full pipeline: vision → plant state → GraphRAG → LLM/fallback."""
    plant = _get_plant_or_404(db, plant_id)
    try:
        analysis = await analysis_service.run_analysis(db, plant, image, symptoms)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # keep unexpected failures visible, not silent 500s
        raise HTTPException(status_code=500,
                            detail=f'Analysis failed: {exc}') from exc
    return plant_service.serialize_analysis(analysis)


@router.get('/{plant_id}/analyses')
def list_analyses(plant_id: int, db: Session = Depends(get_db)):
    _get_plant_or_404(db, plant_id)
    analyses = list(db.scalars(
        select(PlantAnalysis).where(PlantAnalysis.plant_id == plant_id)
        .order_by(PlantAnalysis.created_at.desc())))
    return [plant_service.serialize_analysis(a) for a in analyses]


@router.get('/{plant_id}/care', response_model=list[CareOut])
def list_care(plant_id: int, db: Session = Depends(get_db)):
    _get_plant_or_404(db, plant_id)
    events = list(db.scalars(
        select(CareEvent).where(CareEvent.plant_id == plant_id)
        .order_by(CareEvent.date.desc())))
    return events


@router.post('/{plant_id}/care', response_model=CareOut, status_code=201)
def add_care(plant_id: int, payload: CareInput, db: Session = Depends(get_db)):
    _get_plant_or_404(db, plant_id)
    from datetime import datetime, timezone
    event = CareEvent(
        plant_id=plant_id,
        event_type=payload.event_type,
        description=payload.description,
        date=payload.date or datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
