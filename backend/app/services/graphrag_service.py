"""GraphRAG service — retrieval-grounded recommendation pipeline.

Pipeline (V1):
  Plant State → Entity Identification → KG Retrieval → Document Retrieval
  → Evidence Context → LLM (or deterministic fallback) → Recommendation

The LLM never sees the user's question alone: it is always given the
constructed evidence context, so answers stay grounded and explainable.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from ..models import Plant
from ..config import KNOWLEDGE_DIR
from . import knowledge_service, llm_service, reasoning_engine

DOCUMENTS_DIR = KNOWLEDGE_DIR / 'documents'


def identify_entities(db: Session, plant_state: dict) -> list[dict]:
    """Entity Identification: map plant state signals to knowledge-graph entities."""
    matched: list[dict] = []

    # 1. Species → Plant entity.
    species = plant_state.get('species') or ''
    for e in knowledge_service.find_entities_by_name(db, [species], entity_type='Plant'):
        matched.append({'entity_id': e.id, 'name': e.name, 'entity_type': e.entity_type,
                        'match_reason': f"Plant species: {e.name}"})

    # 2. Symptoms: vision-derived names + keywords from the user's free text.
    symptom_names = list(plant_state.get('symptoms', []))
    reported = (plant_state.get('reported_symptoms_text') or '').lower()
    for e in knowledge_service.list_entities(db, entity_type='Symptom'):
        if e.name.lower() in {s.lower() for s in symptom_names}:
            matched.append({'entity_id': e.id, 'name': e.name, 'entity_type': e.entity_type,
                            'match_reason': 'Detected in image analysis (demo vision model)'})
        elif _name_keywords(e.name) and any(k in reported for k in _name_keywords(e.name)):
            matched.append({'entity_id': e.id, 'name': e.name, 'entity_type': e.entity_type,
                            'match_reason': 'Mentioned in your reported symptoms'})

    # 3. Environmental flags → EnvironmentalCondition entities (exact name match).
    flags_text = ' '.join(plant_state.get('environmental_flags', [])).lower()
    for e in knowledge_service.list_entities(db, entity_type='EnvironmentalCondition'):
        if e.id != 'condition_adequate_light' and e.name.lower() in flags_text:
            matched.append({'entity_id': e.id, 'name': e.name, 'entity_type': e.entity_type,
                            'match_reason': 'Derived from the plant profile'})

    # De-duplicate by entity id, preserving order.
    seen: set[str] = set()
    unique: list[dict] = []
    for m in matched:
        if m['entity_id'] not in seen:
            seen.add(m['entity_id'])
            unique.append(m)
    return unique


def _name_keywords(name: str) -> list[str]:
    words = [w for w in re.split(r'[^a-z]+', name.lower()) if len(w) > 3]
    return words or [name.lower()]


def retrieve_graph_context(db: Session, plant_state: dict) -> dict:
    """Knowledge Graph Retrieval: one-hop neighbourhood of identified entities."""
    identified = identify_entities(db, plant_state)
    entity_ids = [m['entity_id'] for m in identified]
    triples = knowledge_service.neighbors(db, entity_ids, depth=1)
    return {'identified_entities': identified, 'triples': triples}


def retrieve_supporting_documents(graph_context: dict, max_docs: int = 3) -> list[dict]:
    """Document Retrieval: keyword-scored markdown knowledge documents."""
    if not DOCUMENTS_DIR.exists():
        return []
    entity_names = [m['name'].lower() for m in graph_context.get('identified_entities', [])]
    scored: list[dict] = []
    for path in sorted(DOCUMENTS_DIR.glob('*.md')):
        text = path.read_text(encoding='utf-8')
        score = sum(1 for name in entity_names if name in text.lower())
        scored.append({'title': path.stem.replace('_', ' ').title(),
                       'path': str(path), 'score': score, 'text': text})
    scored.sort(key=lambda d: d['score'], reverse=True)
    docs = [d for d in scored if d['score'] > 0][:max_docs]
    if not docs and scored:
        docs = [scored[-1]]  # fall back to the general preventive-care document
    return [{'title': d['title'],
             'excerpt': _excerpt(d['text'])} for d in docs]


def _excerpt(text: str, max_chars: int = 700) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text if len(text) <= max_chars else text[:max_chars].rsplit(' ', 1)[0] + '…'


def build_evidence_context(db: Session, plant_state: dict) -> dict:
    """Evidence Context: the complete grounding package for the LLM / fallback."""
    graph_context = retrieve_graph_context(db, plant_state)
    documents = retrieve_supporting_documents(graph_context)
    return {
        'identified_entities': graph_context['identified_entities'],
        'triples': graph_context['triples'],
        'documents': documents,
    }


def generate_grounded_response(db: Session, plant: Plant, plant_state: dict,
                               evidence: dict) -> dict:
    """Run the LLM if configured, otherwise the deterministic fallback engine.

    Returns the full analysis payload: condition, confidence, explanation,
    recommendations, preventive care, limitations, reasoning mode, llm_summary.
    """
    graph_context = {'triples': evidence['triples']}
    diagnosis = reasoning_engine.diagnose(plant_state, graph_context)
    explanation = reasoning_engine.build_explanation(plant_state, diagnosis)
    recommendations = reasoning_engine.build_recommendations(plant_state, diagnosis, graph_context)
    preventive = reasoning_engine.build_preventive_care(diagnosis, graph_context)
    limitations = reasoning_engine.build_limitations()
    llm_summary = None
    reasoning_mode = reasoning_engine.REASONING_MODE

    if llm_service.is_configured():
        llm_result = llm_service.generate(
            plant_state=plant_state, evidence=evidence, diagnosis=diagnosis)
        if llm_result:
            llm_summary = llm_result['summary']
            reasoning_mode = f"LLM-grounded reasoning ({llm_service.model_name()})"
            if llm_result.get('extra_recommendations'):
                for r in llm_result['extra_recommendations']:
                    recommendations.append({'title': r, 'why': 'Suggested by the LLM using the retrieved evidence.',
                                            'source': 'LLM (grounded on retrieved evidence)',
                                            'priority': 'LLM suggestion'})

    return {
        'predicted_condition': diagnosis['condition'],
        'condition_id': diagnosis.get('condition_id'),
        'confidence': diagnosis['confidence'],
        'explanation': explanation,
        'recommendation': recommendations,
        'preventive_care': preventive,
        'evidence': {
            'identified_entities': evidence['identified_entities'],
            'triples': evidence['triples'],
            'documents': evidence['documents'],
            'runners_up': diagnosis.get('runners_up', []),
        },
        'limitations': limitations,
        'reasoning_mode': reasoning_mode,
        'llm_summary': llm_summary,
    }


