"""Plant State engine.

Combines the plant profile, care history, image analysis and user-reported
symptoms into one structured Plant State object. This is the single object the
GraphRAG retrieval and the reasoning engine consume.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import CareEvent, Plant, PlantAnalysis

RISK_ORDER = {'Low': 0, 'Moderate': 1, 'High': 2, 'Critical': 3}


def build_plant_state(db: Session, plant: Plant, vision: dict,
                      user_symptoms: str | None) -> dict:
    """Fuse profile + vision + reported symptoms + care history into a Plant State."""
    symptoms: list[str] = []
    for s in vision.get('symptoms', []):
        if s not in symptoms:
            symptoms.append(s)

    # Symptoms reported by the user (free text) are matched to KG symptom names
    # later by the GraphRAG entity-identification step; keep the raw text too.
    reported = (user_symptoms or '').strip()

    # Recent care history (last 5 events) feeds personalization.
    care_events = list(db.scalars(
        select_recent_care(plant.id)))[:5]
    care_summary = [
        {'event_type': c.event_type, 'description': c.description,
         'date': c.date.isoformat() if c.date else None}
        for c in care_events
    ]

    # Simple environmental risk flags derived from the profile (demo heuristics).
    env_flags: list[str] = []
    watering = (plant.watering_frequency or '').lower()
    if any(w in watering for w in ('daily', 'every day', 'twice', 'frequent', 'often')):
        env_flags.append('Frequent watering reported (possible excess moisture)')
    light = (plant.light_condition or '').lower()
    if any(w in light for w in ('low', 'shade', 'dim', 'indirect low', 'dark')):
        env_flags.append('Low light reported')
    if any(w in light for w in ('full sun', 'bright', 'direct')):
        env_flags.append('Bright light reported')

    risk = compute_risk(symptoms, vision.get('confidence', 0.0), env_flags)

    return {
        'plant_id': plant.id,
        'name': plant.name,
        'species': plant.species,
        'growth_stage': plant.growth_stage,
        'age_days': plant.age_days,
        'watering_frequency': plant.watering_frequency,
        'light_condition': plant.light_condition,
        'notes': plant.notes or '',
        'symptoms': symptoms,
        'reported_symptoms_text': reported,
        'environmental_flags': env_flags,
        'care_history': care_summary,
        'vision_confidence': vision.get('confidence', 0.0),
        'risk_level': risk,
    }


def select_recent_care(plant_id: int):
    from sqlalchemy import select
    return select(CareEvent).where(CareEvent.plant_id == plant_id)\
        .order_by(CareEvent.date.desc()).limit(5)


def previous_analyses(db: Session, plant: Plant, limit: int = 3) -> list[PlantAnalysis]:
    from sqlalchemy import select
    return list(db.scalars(
        select(PlantAnalysis).where(PlantAnalysis.plant_id == plant.id)
        .order_by(PlantAnalysis.created_at.desc()).limit(limit)))


def compute_risk(symptoms: list[str], confidence: float, env_flags: list[str]) -> str:
    """Deterministic demo risk level from evidence volume and profile flags."""
    signals = len(symptoms) + len(env_flags)
    if signals == 0:
        return 'Low'
    if signals >= 4 or (signals >= 3 and confidence >= 0.75):
        return 'High'
    if signals >= 2:
        return 'Moderate'
    return 'Low'
