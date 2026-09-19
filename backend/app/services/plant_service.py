"""Plant serialization and demo health-status computation."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Plant

# Conditions considered healthy for status badges.
HEALTHY_MARKERS = ('no visible disease', 'inconclusive')


def latest_analysis(plant: Plant):
    return plant.analyses[0] if plant.analyses else None


def health_status(plant: Plant) -> str:
    latest = latest_analysis(plant)
    if latest is None:
        return 'New'
    if any(m in latest.predicted_condition.lower() for m in HEALTHY_MARKERS):
        return 'Healthy'
    risk = (latest.plant_state or {}).get('risk_level', '')
    if risk in ('High', 'Critical'):
        return 'Needs Attention'
    if any(m in latest.predicted_condition.lower() for m in ('overwatering', 'deficiency')):
        return 'Monitor'
    return 'Monitor'


def serialize_plant(db: Session, plant: Plant) -> dict:
    latest = latest_analysis(plant)
    latest_state = (latest.plant_state or {}) if latest else {}
    return {
        'id': plant.id,
        'name': plant.name,
        'species': plant.species,
        'growth_stage': plant.growth_stage,
        'age_days': plant.age_days,
        'watering_frequency': plant.watering_frequency,
        'light_condition': plant.light_condition,
        'notes': plant.notes,
        'is_demo': plant.is_demo,
        'created_at': plant.created_at,
        'updated_at': plant.updated_at,
        'health_status': health_status(plant),
        'risk_level': latest_state.get('risk_level'),
        'last_analysis': latest.created_at if latest else None,
        'latest_condition': latest.predicted_condition if latest else None,
        'analysis_count': len(plant.analyses),
        'image_path': latest.image_path if latest else None,
    }


def serialize_analysis(a) -> dict:
    return {
        'id': a.id,
        'plant_id': a.plant_id,
        'plant_name': a.plant.name if a.plant else None,
        'image_path': a.image_path,
        'detected_symptoms': a.detected_symptoms or [],
        'predicted_condition': a.predicted_condition,
        'confidence': a.confidence,
        'plant_state': a.plant_state or {},
        'explanation': a.explanation or [],
        'recommendation': a.recommendation or [],
        'preventive_care': a.preventive_care or [],
        'evidence': a.evidence or {},
        'limitations': a.limitations or [],
        'model_status': a.model_status,
        'reasoning_mode': a.reasoning_mode,
        'llm_summary': a.llm_summary,
        'is_demo': a.is_demo,
        'created_at': a.created_at,
    }
