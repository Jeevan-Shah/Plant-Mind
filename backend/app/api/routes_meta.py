"""Dashboard stats, system health and demo-data management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import __version__
from ..config import GRAPH_BACKEND
from ..database import get_db
from ..models import Plant, PlantAnalysis
from ..schemas import DashboardStats, HealthCheck
from ..services import llm_service, plant_service, reasoning_engine, vision_service

router = APIRouter(prefix='/api', tags=['system'])


@router.get('/health', response_model=HealthCheck)
def health(db: Session = Depends(get_db)):
    try:
        db.scalar(select(func.count()).select_from(Plant))
        database = 'connected'
    except Exception:
        database = 'unavailable'
    return HealthCheck(
        status='ok' if database == 'connected' else 'degraded',
        version=__version__,
        database=database,
        graph_backend=GRAPH_BACKEND,
        vision_model=f'Demo Vision Model ({vision_service.MODEL_STATUS})',
        llm_configured=llm_service.is_configured(),
        reasoning_mode=('LLM + KG fallback' if llm_service.is_configured()
                        else reasoning_engine.REASONING_MODE),
    )


@router.get('/dashboard/stats', response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    plants = list(db.scalars(select(Plant).order_by(Plant.created_at.desc())))
    total_analyses = db.scalar(select(func.count()).select_from(PlantAnalysis)) or 0

    breakdown = {'Healthy': 0, 'Monitor': 0, 'Needs Attention': 0, 'New': 0}
    for p in plants:
        status = plant_service.health_status(p)
        breakdown[status] = breakdown.get(status, 0) + 1

    recent_conditions = []
    recent = list(db.scalars(select(PlantAnalysis)
                             .order_by(PlantAnalysis.created_at.desc()).limit(5)))
    for a in recent:
        recent_conditions.append({
            'analysis_id': a.id,
            'plant_id': a.plant_id,
            'plant_name': a.plant.name if a.plant else None,
            'condition': a.predicted_condition,
            'confidence': a.confidence,
            'risk_level': (a.plant_state or {}).get('risk_level'),
            'created_at': a.created_at,
        })
    return DashboardStats(
        total_plants=len(plants),
        total_analyses=total_analyses,
        needs_attention=breakdown.get('Needs Attention', 0),
        healthy=breakdown.get('Healthy', 0),
        monitor=breakdown.get('Monitor', 0),
        new_plants=breakdown.get('New', 0),
        status_breakdown=breakdown,
        recent_conditions=recent_conditions,
    )


@router.post('/demo/reset')
def reset_demo(db: Session = Depends(get_db)):
    """Delete ALL plants/analyses/care events and reseed the demo data.

    Knowledge entities/relationships are preserved (they are the demo KG).
    Intended for development demos only.
    """
    from backend.seed import seed_demo_data
    db.query(PlantAnalysis).delete()
    for p in list(db.scalars(select(Plant))):
        db.delete(p)
    db.commit()
    created = seed_demo_data(db)
    return {'status': 'ok', 'demo_plants_created': created}
