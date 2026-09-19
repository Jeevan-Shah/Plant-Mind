"""Analysis orchestration: the end-to-end pipeline for one plant analysis.

Image + plant profile + care history + symptoms
  → vision (demo) → Plant State → GraphRAG evidence → LLM/fallback
  → explainable, personalized recommendation → persisted PlantAnalysis
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..models import CareEvent, Plant, PlantAnalysis
from . import graphrag_service, plant_state_service, vision_service

ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
MAX_SIZE_BYTES = 8 * 1024 * 1024


async def run_analysis(db: Session, plant: Plant, image: UploadFile,
                       symptoms: str | None) -> PlantAnalysis:
    """Execute the full pipeline and persist the result."""
    image_bytes = await image.read()
    if not image_bytes:
        raise ValueError('No image was uploaded.')
    if len(image_bytes) > MAX_SIZE_BYTES:
        raise ValueError('Image is larger than the 8 MB limit.')
    content_type = (image.content_type or '').lower()
    if content_type and content_type not in ALLOWED_TYPES:
        raise ValueError(f'Unsupported image type "{image.content_type}". '
                         'Use JPEG, PNG, WebP or GIF.')

    # 1. Computer vision (demo model in V1).
    vision = vision_service.analyze_image(image_bytes)

    # 2. Persist the upload.
    suffix = _suffix_for(image)
    image_path = UPLOAD_DIR / f'{uuid.uuid4().hex}{suffix}'
    image_path.write_bytes(image_bytes)

    # 3. Plant State engine.
    plant_state = plant_state_service.build_plant_state(db, plant, vision, symptoms)

    # 4. GraphRAG: entity identification + KG retrieval + document retrieval.
    evidence = graphrag_service.build_evidence_context(db, plant_state)

    # 5. LLM (if configured) or deterministic KG fallback reasoning.
    result = graphrag_service.generate_grounded_response(db, plant, plant_state, evidence)

    # 6. Persist the analysis + an observation care event.
    analysis = PlantAnalysis(
        plant_id=plant.id,
        image_path=f'uploads/{image_path.name}',
        detected_symptoms=plant_state['symptoms'],
        predicted_condition=result['predicted_condition'],
        confidence=result['confidence'],
        plant_state=plant_state,
        explanation=result['explanation'],
        recommendation=result['recommendation'],
        preventive_care=result['preventive_care'],
        evidence=result['evidence'],
        limitations=result['limitations'],
        model_status=vision.get('model_status', 'demo'),
        reasoning_mode=result['reasoning_mode'],
        llm_summary=result.get('llm_summary'),
        is_demo=vision.get('model_status', 'demo') == 'demo',
    )
    db.add(analysis)
    db.add(CareEvent(
        plant_id=plant.id,
        event_type='Observation',
        description=f'Analysis performed: {result["predicted_condition"]} '
                    f'(demo confidence {int(round(result["confidence"] * 100))}%).',
        date=datetime.now(timezone.utc),
    ))
    db.commit()
    db.refresh(analysis)
    return analysis


def _suffix_for(image: UploadFile) -> str:
    name = image.filename or ''
    if '.' in name:
        ext = '.' + name.rsplit('.', 1)[-1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            return '.jpg' if ext in ('.jpeg', '.jpg') else ext
    return '.jpg'
