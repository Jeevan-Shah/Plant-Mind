"""Knowledge graph service — the graph abstraction layer for PlantMind.

V1 stores the graph in SQLite via the KnowledgeEntity / KnowledgeRelationship
models and seeds it from knowledge/entities.json + relationships.json.
The public interface below (get_entity, search_entities, get_relationships,
neighbors, find_entities_by_name, all_triples) is backend-agnostic so a real
Neo4j driver can be dropped in behind GRAPH_BACKEND=neo4j later without
touching the GraphRAG service, the reasoning engine, or the API layer.
"""
from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import GRAPH_BACKEND, KNOWLEDGE_DIR
from ..models import KnowledgeEntity, KnowledgeRelationship

SEED_ENTITIES_PATH = KNOWLEDGE_DIR / 'entities.json'
SEED_RELATIONSHIPS_PATH = KNOWLEDGE_DIR / 'relationships.json'


def _neo4j_unavailable() -> None:
    """Neo4j driver integration point for a future version. V1 uses SQLite."""
    if GRAPH_BACKEND == 'neo4j':
        raise NotImplementedError(
            'Neo4j backend is planned but not enabled in V1; '
            "set GRAPH_BACKEND=sqlite (default) to use the local fallback graph."
        )


def seed_knowledge_if_empty(db: Session) -> bool:
    """Load entities/relationships from the JSON knowledge base if tables are empty."""
    _neo4j_unavailable()
    if db.scalar(select(KnowledgeEntity.id).limit(1)):
        return False
    entities = json.loads(SEED_ENTITIES_PATH.read_text(encoding='utf-8'))['entities']
    rels = json.loads(SEED_RELATIONSHIPS_PATH.read_text(encoding='utf-8'))['relationships']
    for e in entities:
        db.add(KnowledgeEntity(id=e['id'], entity_type=e['entity_type'],
                               name=e['name'], description=e['description']))
    db.flush()
    for r in rels:
        db.add(KnowledgeRelationship(source_entity_id=r['source'],
                                     relationship=r['relationship'],
                                     target_entity_id=r['target']))
    db.commit()
    return True


def entity_dict(e: KnowledgeEntity) -> dict:
    return {'id': e.id, 'entity_type': e.entity_type, 'name': e.name,
            'description': e.description}


def triple_dict(r: KnowledgeRelationship, entities: dict[str, KnowledgeEntity]) -> dict:
    src = entities.get(r.source_entity_id)
    tgt = entities.get(r.target_entity_id)
    return {
        'source': r.source_entity_id,
        'source_name': src.name if src else r.source_entity_id,
        'source_type': src.entity_type if src else 'Unknown',
        'relationship': r.relationship,
        'target': r.target_entity_id,
        'target_name': tgt.name if tgt else r.target_entity_id,
        'target_type': tgt.entity_type if tgt else 'Unknown',
    }


def get_entity(db: Session, entity_id: str) -> KnowledgeEntity | None:
    _neo4j_unavailable()
    return db.get(KnowledgeEntity, entity_id)


def list_entities(db: Session, entity_type: str | None = None,
                  q: str | None = None, limit: int = 200) -> list[KnowledgeEntity]:
    _neo4j_unavailable()
    stmt = select(KnowledgeEntity).order_by(KnowledgeEntity.entity_type, KnowledgeEntity.name)
    if entity_type:
        stmt = stmt.where(KnowledgeEntity.entity_type == entity_type)
    if q:
        like = f'%{q}%'
        stmt = stmt.where(or_(KnowledgeEntity.name.ilike(like),
                              KnowledgeEntity.description.ilike(like)))
    return list(db.scalars(stmt.limit(limit)))


def get_relationships(db: Session, entity_id: str) -> dict:
    """All outgoing and incoming relationships of one entity."""
    _neo4j_unavailable()
    outgoing = list(db.scalars(select(KnowledgeRelationship)
                               .where(KnowledgeRelationship.source_entity_id == entity_id)))
    incoming = list(db.scalars(select(KnowledgeRelationship)
                               .where(KnowledgeRelationship.target_entity_id == entity_id)))
    ids = ({entity_id}
           | {r.source_entity_id for r in outgoing} | {r.target_entity_id for r in outgoing}
           | {r.source_entity_id for r in incoming} | {r.target_entity_id for r in incoming})
    emap = {e.id: e for e in db.scalars(select(KnowledgeEntity)
                                        .where(KnowledgeEntity.id.in_(ids)))}
    return {
        'entity': emap.get(entity_id) and entity_dict(emap[entity_id]),
        'outgoing': [triple_dict(r, emap) for r in outgoing],
        'incoming': [triple_dict(r, emap) for r in incoming],
    }


def find_entities_by_name(db: Session, names: Iterable[str],
                          entity_type: str | None = None) -> list[KnowledgeEntity]:
    """Find KG entities whose name matches any of the given names (case-insensitive)."""
    _neo4j_unavailable()
    wanted = {n.strip().lower() for n in names if n and n.strip()}
    if not wanted:
        return []
    stmt = select(KnowledgeEntity)
    if entity_type:
        stmt = stmt.where(KnowledgeEntity.entity_type == entity_type)
    return [e for e in db.scalars(stmt) if e.name.lower() in wanted]


def neighbors(db: Session, entity_ids: Iterable[str], depth: int = 1) -> list[dict]:
    """Expand around the given entities as triples.

    depth=1 returns the seed entities' direct triples plus one expansion pass
    from the newly discovered nodes (e.g. Plant -> Disease -> managedBy ->
    Treatment), which is what the GraphRAG evidence context needs.
    """
    _neo4j_unavailable()
    frontier = {i for i in entity_ids if i}
    collected: dict[int, KnowledgeRelationship] = {}
    seen = set(frontier)
    for _ in range(max(1, depth) + 1):
        if not frontier:
            break
        rels = list(db.scalars(select(KnowledgeRelationship).where(
            or_(KnowledgeRelationship.source_entity_id.in_(frontier),
                KnowledgeRelationship.target_entity_id.in_(frontier)))))
        for r in rels:
            collected[r.id] = r
        nxt = set()
        for r in rels:
            for endpoint in (r.source_entity_id, r.target_entity_id):
                if endpoint not in seen:
                    nxt.add(endpoint)
        seen |= nxt
        frontier = nxt
    ids = seen
    emap = {e.id: e for e in db.scalars(select(KnowledgeEntity)
                                        .where(KnowledgeEntity.id.in_(ids)))} if ids else {}
    return [triple_dict(r, emap) for r in sorted(collected.values(), key=lambda x: x.id)]
