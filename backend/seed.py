"""Seeding utilities: demo knowledge base and demo plants.

Run directly with:  python backend/seed.py
The knowledge graph is seeded automatically on startup if empty.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from backend.app.models import CareEvent, Plant  # noqa: E402
from backend.app.services import knowledge_service  # noqa: E402


def seed_demo_data(db: Session) -> int:
    """Insert demo plants + care history if no plants exist. Returns count created."""
    if db.query(Plant).count() > 0:
        return 0

    now = datetime.now(timezone.utc)
    plants = [
        Plant(name='Tomato #17', species='Tomato', growth_stage='Flowering', age_days=42,
              watering_frequency='Every 2 days', light_condition='Bright, indirect (balcony)',
              notes='Container plant on the balcony; lower leaves starting to look pale.',
              is_demo=True,
              created_at=now - timedelta(days=42), updated_at=now - timedelta(days=42)),
        Plant(name='Rose #03', species='Rose', growth_stage='Vegetative', age_days=120,
              watering_frequency='Every 3 days', light_condition='Full sun (6h+)',
              notes='Repotted this spring. New shoots look healthy.',
              is_demo=True,
              created_at=now - timedelta(days=120), updated_at=now - timedelta(days=120)),
        Plant(name='Potato #08', species='Potato', growth_stage='Vegetative', age_days=30,
              watering_frequency='Every 2 days', light_condition='Full sun (garden bed)',
              notes='Grown in a grow bag; watching for early blight like last season.',
              is_demo=True,
              created_at=now - timedelta(days=30), updated_at=now - timedelta(days=30)),
        Plant(name='Apple (Dwarf) #01', species='Apple', growth_stage='Mature', age_days=730,
              watering_frequency='Twice a week', light_condition='Full sun (terrace)',
              notes='Dwarf variety in a large pot. Some leaf spotting last autumn.',
              is_demo=True,
              created_at=now - timedelta(days=730), updated_at=now - timedelta(days=730)),
    ]
    db.add_all(plants)
    db.flush()

    events = [
        CareEvent(plant_id=plants[0].id, event_type='Watering',
                  description='Watered thoroughly until runoff.', date=now - timedelta(days=1)),
        CareEvent(plant_id=plants[0].id, event_type='Fertilizing',
                  description='Half-strength tomato feed.', date=now - timedelta(days=6)),
        CareEvent(plant_id=plants[0].id, event_type='Observation',
                  description='Lower leaves pale; slight yellowing noticed.',
                  date=now - timedelta(days=2)),
        CareEvent(plant_id=plants[1].id, event_type='Pruning',
                  description='Removed two old stems to open up the centre.',
                  date=now - timedelta(days=4)),
        CareEvent(plant_id=plants[1].id, event_type='Watering',
                  description='Deep watering in the morning.', date=now - timedelta(days=2)),
        CareEvent(plant_id=plants[2].id, event_type='Watering',
                  description='Grow bag moistened; checked drainage.', date=now - timedelta(days=1)),
        CareEvent(plant_id=plants[3].id, event_type='Observation',
                  description='A few leaves with small brown spots on the north side.',
                  date=now - timedelta(days=3)),
    ]
    db.add_all(events)
    db.commit()
    return len(plants)


def seed_all(db: Session) -> dict:
    kg_seeded = knowledge_service.seed_knowledge_if_empty(db)
    plants_created = seed_demo_data(db)
    return {'knowledge_graph_seeded': kg_seeded, 'demo_plants_created': plants_created}


if __name__ == '__main__':
    from backend.app.database import Base, SessionLocal, engine
    from backend.app import models  # noqa: F401  (register models)

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        result = seed_all(session)
    print(f'Seeding complete: {result}')

