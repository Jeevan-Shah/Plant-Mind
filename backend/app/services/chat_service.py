"""Follow-up chat service - grounded Q&A over a completed analysis.

After a result is shown the user may have further doubts ("How often should I
water it?", "Is this serious?", "Will it spread?"). This service answers them
with the same explainability contract as the rest of the pipeline:

  1. Retrieve evidence focused on the question: question keywords -> knowledge
     graph entity lookup -> neighbourhood triples + supporting documents,
     merged with the evidence already stored on the analysis.
  2. If an LLM is configured, answer strictly from that evidence + the stored
     analysis (llm_service.chat).
  3. Otherwise a deterministic intent-based fallback composes an answer from
     the analysis, the plant profile and the retrieved triples, always listing
     the sources that were used.

The endpoint is stateless: the client sends the full conversation history and
this service answers only the final user turn.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from ..models import PlantAnalysis
from . import graphrag_service, knowledge_service, llm_service, plant_service

STOPWORDS = {
    'the', 'and', 'for', 'are', 'was', 'were', 'this', 'that', 'with', 'from',
    'have', 'has', 'had', 'not', 'but', 'you', 'your', 'can', 'could', 'would',
    'should', 'will', 'shall', 'about', 'there', 'their', 'they', 'them', 'then',
    'than', 'when', 'what', 'which', 'who', 'how', 'why', 'where', 'into', 'out',
    'its', 'our', 'his', 'her', 'been', 'been', 'does', 'did', 'doing', 'very',
    'just', 'also', 'any', 'all', 'some', 'please', 'tell', 'want', 'need',
    'know', 'let', 'get', 'got', 'make', 'made', 'plant', 'plantmind', 'much',
    'many', 'more', 'most', 'over', 'under', 'still', 'even', 'one', 'two',
}

# Keyword buckets for the deterministic fallback, evaluated in order.
INTENT_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ('watering', ('water', 'watering', 'irrigat', 'moist', 'thirsty', 'hydrate')),
    ('spread', ('spread', 'contagious', 'contagion', 'infect', 'other plants',
                'transfer', 'isolate', 'quarantine')),
    ('severity', ('serious', 'severe', 'how bad', 'dangerous', 'urgent', 'die',
                  'death', 'kill', 'worse', 'critical', 'emergency')),
    ('treatment', ('treatment', 'treat', 'cure', 'fix', 'heal', 'spray',
                   'fungicide', 'pesticide', 'medicine', 'remedy', 'pest',
                   'bug', 'insect', 'remove', 'get rid')),
    ('light', ('light', 'sun', 'sunlight', 'shade', 'window', 'dark')),
    ('fertilizer', ('fertiliz', 'feed', 'nutrient', 'manure', 'compost', 'npk')),
    ('repotting', ('repot', 'transplant', 'root', 'drainage', 'potting', 'soil')),
    ('prevention', ('prevent', 'avoid', 'protect', 'stop it', 'future',
                    'again', 'next time')),
    ('recovery', ('recover', 'how long', 'how many days', 'how many weeks',
                  'time to', 'weeks', 'timeline')),
    ('confidence', ('why', 'confidence', 'sure', 'certain', 'accurate',
                    'correct', 'really', 'prove', 'proof')),
]


def _keywords(text: str) -> list[str]:
    """Meaningful tokens from the question, most distinctive first."""
    words = [w for w in re.split(r'[^a-z]+', text.lower())
             if len(w) > 2 and w not in STOPWORDS]
    seen: set[str] = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:8]


def _detect_intent(question: str) -> str:
    q = question.lower()
    if re.search(r'\b(hi|hello|hey|greetings|good morning|good evening)\b', q):
        return 'greeting'
    for name, keys in INTENT_KEYWORDS:
        if any(k in q for k in keys):
            return name
    return 'general'


def _retrieve_documents(keywords: list[str], entities: list[dict],
                        max_docs: int = 3) -> list[dict]:
    """Keyword-scored markdown documents (same corpus the GraphRAG uses)."""
    if not graphrag_service.DOCUMENTS_DIR.exists():
        return []
    names = [e['name'].lower() for e in entities if e.get('name')]
    scored: list[dict] = []
    for path in sorted(graphrag_service.DOCUMENTS_DIR.glob('*.md')):
        text = path.read_text(encoding='utf-8')
        low = text.lower()
        score = sum(2 for n in names if n in low) + sum(1 for k in keywords if k in low)
        scored.append({'title': path.stem.replace('_', ' ').title(),
                       'score': score, 'text': text})
    scored.sort(key=lambda d: d['score'], reverse=True)
    docs = [d for d in scored if d['score'] > 0][:max_docs]
    if not docs and scored:
        docs = [scored[0]]  # general care document as a last resort
    return [{'title': d['title'],
             'excerpt': graphrag_service._excerpt(d['text'])} for d in docs]


def retrieve_for_question(db: Session, analysis: PlantAnalysis,
                          question: str) -> dict:
    """Question-focused retrieval merged with the analysis' stored evidence."""
    stored = analysis.evidence or {}
    keywords = _keywords(question)
    matched: dict[str, dict] = {}

    # Entities already identified when the analysis ran.
    for e in stored.get('identified_entities') or []:
        eid = e.get('entity_id') or e.get('id')
        if eid:
            matched[eid] = {'id': eid, 'entity_type': e.get('entity_type', 'Unknown'),
                            'name': e.get('name', eid), 'description': ''}

    # Fresh keyword lookup against the KG (name/description search).
    for kw in keywords[:6]:
        for e in knowledge_service.list_entities(db, q=kw, limit=8):
            matched.setdefault(e.id, knowledge_service.entity_dict(e))

    # The predicted condition itself.
    condition = analysis.predicted_condition or ''
    for e in knowledge_service.find_entities_by_name(db, [condition],
                                                     entity_type='Disease'):
        matched.setdefault(e.id, knowledge_service.entity_dict(e))

    # Neighbourhood triples, plus whatever the stored analysis already found.
    triples = knowledge_service.neighbors(db, list(matched), depth=1) if matched else []
    seen = {(t['source'], t['relationship'], t['target']) for t in triples}
    for t in stored.get('triples') or []:
        key = (t['source'], t['relationship'], t['target'])
        if key not in seen:
            triples.append(t)
            seen.add(key)

    documents = _retrieve_documents(keywords, list(matched.values()))
    return {'keywords': keywords, 'entities': list(matched.values()),
            'triples': triples, 'documents': documents}
# ---------------------------------------------------------------------------
# Deterministic (offline) fallback answers
# ---------------------------------------------------------------------------

def _add_source(sources: list[dict], label: str, detail: str) -> None:
    """Append a source chip, de-duplicated by label+detail."""
    if detail and not any(s['label'] == label and s['detail'] == detail for s in sources):
        sources.append({'label': label, 'detail': detail})


def _triple_line(t: dict) -> str:
    return f"{t['source_name']} -{t['relationship']}-> {t['target_name']}"


def _matching_triples(context: dict, keywords: tuple[str, ...], limit: int = 4) -> list[dict]:
    hits = []
    for t in context['triples']:
        hay = f"{t['source_name']} {t['relationship']} {t['target_name']}".lower()
        if any(k in hay for k in keywords):
            hits.append(t)
    return hits[:limit]


def _matching_entities(context: dict, keywords: tuple[str, ...], limit: int = 3) -> list[dict]:
    hits = []
    for e in context['entities']:
        hay = f"{e['name']} {e.get('description', '')}".lower()
        if any(k in hay for k in keywords):
            hits.append(e)
    return hits[:limit]


def _graph_evidence_lines(context: dict, keywords: tuple[str, ...],
                          sources: list[dict]) -> list[str]:
    """Render matching KG triples into answer lines + source chips."""
    lines = []
    for t in _matching_triples(context, keywords):
        line = _triple_line(t)
        lines.append(line)
        _add_source(sources, 'Knowledge graph', line)
    return lines


def _entity_notes(context: dict, keywords: tuple[str, ...],
                  sources: list[dict]) -> list[str]:
    """Descriptions of KG entities matching the keywords."""
    notes = []
    for e in _matching_entities(context, keywords):
        desc = (e.get('description') or '').strip()
        if desc:
            notes.append(desc if desc.endswith('.') else desc + '.')
        _add_source(sources, 'KG entity', f"{e['name']} ({e.get('entity_type', '?')})")
    return notes


def _doc_notes(context: dict, keywords: tuple[str, ...],
               sources: list[dict]) -> list[str]:
    notes = []
    for d in context['documents']:
        low = (d['title'] + ' ' + d['excerpt']).lower()
        if any(k in low for k in keywords):
            sentence = d['excerpt'].strip().split('\n')[0][:220]
            notes.append(f"{d['title']}: {sentence}")
            _add_source(sources, 'Document', d['title'])
    return notes[:2]


def _fallback_answer(analysis: dict, context: dict, question: str) -> tuple[str, list[dict]]:
    """Intent-based answer composed only from the analysis + retrieved KG data."""
    intent = _detect_intent(question)
    state = analysis.get('plant_state') or {}
    condition = analysis.get('predicted_condition') or 'the flagged condition'
    plant = analysis.get('plant_name') or state.get('name') or 'your plant'
    species = state.get('species') or ''
    confidence = round((analysis.get('confidence') or 0) * 100)
    risk = state.get('risk_level') or 'unknown'
    symptoms = analysis.get('detected_symptoms') or []
    recs = analysis.get('recommendation') or []
    sources: list[dict] = []
    parts: list[str] = []

    if intent == 'greeting':
        return (
            f"Hi! I'm the PlantMind care assistant for {plant}. This report points to "
            f"a POSSIBLE case of {condition} ({confidence}% demo confidence). Ask me about "
            "watering, light, treatment, spread risk, prevention, or why this diagnosis "
            "was chosen.", [] )

    if intent == 'watering':
        parts.append(
            f"Watering {plant} ({species}): your profile says \"{state.get('watering_frequency', 'not set')}\".")
        flags = state.get('environmental_flags') or []
        excess = [f for f in flags if 'water' in f.lower() or 'moisture' in f.lower()]
        if excess:
            parts.append(f"Note: {excess[0]} - check the top 2-3 cm of soil before watering again.")
        else:
            parts.append("Check the top 2-3 cm of soil with a finger: water only when it feels dry.")
        graph = _graph_evidence_lines(context, ('water', 'moist', 'irrigat', 'soil', 'dry', 'damp'), sources)
        if graph:
            parts.append("Knowledge-graph evidence:\n- " + "\n- ".join(graph))
        notes = _entity_notes(context, ('water', 'soil', 'root'), sources)
        if notes:
            parts.append("Knowledge note: " + " ".join(notes))

    elif intent == 'light':
        parts.append(
            f"Light for {plant}: the profile says \"{state.get('light_condition', 'not set')}\".")
        graph = _graph_evidence_lines(context, ('light', 'sun', 'shade', 'temperature', 'indoor'), sources)
        if graph:
            parts.append("Knowledge-graph evidence:\n- " + "\n- ".join(graph))
        notes = _entity_notes(context, ('light', 'sun', 'shade'), sources)
        if notes:
            parts.append("Knowledge note: " + " ".join(notes))
        if not graph and not notes:
            parts.append("The knowledge base has no light specifics for this condition; "
                         f"keep the current setting (\"{state.get('light_condition', 'unknown')}\") "
                         "and watch how the symptoms evolve.")

    elif intent == 'treatment':
        treatments = [t for t in context['triples']
                      if t.get('target_type') == 'Treatment'
                      or 'treat' in t['relationship'].lower()
                      or 'managed' in t['relationship'].lower()
                      or 'control' in t['relationship'].lower()]
        if treatments:
            parts.append(f"For {condition}, the knowledge graph recommends:")
            for t in treatments[:4]:
                line = _triple_line(t)
                parts.append(f"- {line}")
                _add_source(sources, 'Knowledge graph', line)
        else:
            notes = _entity_notes(context, ('treat', 'spray', 'cure', 'remove', 'prune'), sources)
            if notes:
                parts.append("Knowledge notes:\n- " + "\n- ".join(notes))
            else:
                parts.append(f"The knowledge base has no specific treatment entry for {condition} "
                             "on this plant species - start with the recommended actions below "
                             "and re-analyze in a few days.")
        if recs:
            parts.append("Do this first: " + "; ".join(r['title'] for r in recs[:2]) + ".")

    elif intent == 'spread':
        graph = _graph_evidence_lines(context, ('spread', 'infect', 'contagio', 'transmit',
                                                 'humid', 'spore'), sources)
        if graph:
            parts.append(f"What the knowledge graph says about spreading:\n- " + "\n- ".join(graph))
        else:
            parts.append(f"The knowledge base does not record spread behaviour for {condition} "
                         f"on {species or 'this species'}, so I cannot confirm the risk from "
                         "evidence alone.")
        parts.append("As a general precaution (not KG evidence): isolate the plant, avoid "
                     "touching leaves back-to-back, and disinfect scissors between plants.")
        _add_source(sources, 'General hygiene advice', 'Not drawn from the knowledge graph')

    elif intent == 'severity':
        parts.append(
            f"Plant-state risk is {risk} and the demo confidence for {condition} is {confidence}%. "
            "This is a POSSIBLE diagnosis from a photo + knowledge graph, not a lab confirmation.")
        lims = analysis.get('limitations') or []
        if lims:
            parts.append(f"Important limitation: {lims[0]}")
            _add_source(sources, 'Limitation', lims[0])
        if symptoms:
            parts.append(f"Detected symptoms: {', '.join(symptoms)}.")
        if recs:
            parts.append("Next step: " + recs[0]['title'] + ". " + recs[0]['why'])
            _add_source(sources, 'Recommendation', recs[0].get('source', 'analysis'))

    elif intent == 'confidence':
        parts.append(
            f"Why {condition}: the vision step saw {', '.join(symptoms) if symptoms else 'no distinct symptoms'} "
            "in the photo, the plant-state engine merged that with this profile and its care "
            "history, and the knowledge graph was searched for conditions matching those signals.")
        entities = (analysis.get('evidence') or {}).get('identified_entities') or []
        if entities:
            names = ', '.join(e['name'] for e in entities[:4])
            parts.append(f"Matched KG entities: {names}.")
            for e in entities[:3]:
                _add_source(sources, 'KG entity', f"{e['name']} ({e.get('entity_type', '?')})")
        expl = analysis.get('explanation') or []
        if expl:
            parts.append(expl[0])
            _add_source(sources, 'Explanation', 'From the reasoning engine')
        runners = (analysis.get('evidence') or {}).get('runners_up') or []
        if runners:
            parts.append("Other candidates considered: "
                         + ', '.join(f"{r['condition']} (match score {r['score']:.1f})" for r in runners[:3]) + ".")
        parts.append(f"Confidence is {confidence}% as a demo value - treat it as a ranking, not a probability.")

    elif intent == 'prevention':
        preventive = analysis.get('preventive_care') or []
        if preventive:
            parts.append(f"To prevent {condition} from returning:")
            for p in preventive[:3]:
                parts.append(f"- {p['title']}")
                _add_source(sources, 'Preventive care', p.get('source', 'analysis'))
        else:
            parts.append("The analysis did not produce preventive-care items for this case.")
        graph = _graph_evidence_lines(context, ('prevent', 'avoid', 'hygien', 'rotat'), sources)
        if graph:
            parts.append("Knowledge-graph evidence:\n- " + "\n- ".join(graph))

    elif intent == 'fertilizer':
        graph = _graph_evidence_lines(context, ('fertiliz', 'nutrient', 'feed', 'compost', 'soil'), sources)
        notes = _entity_notes(context, ('fertiliz', 'nutrient', 'feed', 'compost'), sources)
        if graph or notes:
            parts.append("What the knowledge base says:")
            parts.extend("- " + x for x in graph + notes)
        else:
            parts.append(f"The knowledge base has no fertilizer guidance tied to {condition}. "
                         "While a plant is stressed, hold off on fertilizer and focus on the "
                         "recommended actions above; resume feeding after it recovers. "
                         "(General advice - not KG evidence.)")
            _add_source(sources, 'General advice', 'Not drawn from the knowledge graph')

    elif intent == 'repotting':
        graph = _graph_evidence_lines(context, ('soil', 'drainage', 'repot', 'root', 'pot'), sources)
        if graph:
            parts.append(f"Knowledge-graph evidence for repotting/soil:\n- " + "\n- ".join(graph))
        else:
            parts.append("The knowledge base has no repotting entry for this condition. "
                         "If roots crowd the pot or drainage is poor, repot only after the "
                         "current stress episode settles. (General advice - not KG evidence.)")
            _add_source(sources, 'General advice', 'Not drawn from the knowledge graph')

    elif intent == 'recovery':
        parts.append("The knowledge base does not give a fixed timeline for this condition, "
                     "so an honest estimate is not possible from the evidence.")
        parts.append("Track progress by re-analyzing a photo every few days: if "
                     f"{', '.join(symptoms[:2]) if symptoms else 'the symptoms'} fade and new "
                     "growth appears, recovery is on track; if they spread, treat it as worsening.")
        if recs:
            parts.append("Meanwhile: " + recs[0]['title'] + ".")

    else:  # general
        head = (f"Short version: {plant} ({species}) shows "
                f"{', '.join(symptoms) if symptoms else 'no distinct symptoms'} and the system "
                f"flags a POSSIBLE {condition} - {confidence}% demo confidence, {risk} plant-state risk.")
        parts.append(head)
        expl = analysis.get('explanation') or []
        if expl:
            parts.append(expl[0])
            _add_source(sources, 'Explanation', 'From the reasoning engine')
        if recs:
            parts.append("Do this first:")
            parts.extend(f"{i + 1}) {r['title']}" for i, r in enumerate(recs[:2]))
        notes = _doc_notes(context, context['keywords'] or ('care',), sources)
        if notes:
            parts.append("From the knowledge documents:\n- " + "\n- ".join(notes))
        parts.append("You can also ask about watering, light, treatment, spread risk, "
                     "prevention, or why this diagnosis was chosen.")

    return ('\n'.join(p for p in parts if p).strip(), sources)


def answer(db: Session, analysis: PlantAnalysis, messages: list[dict]) -> dict:
    """Answer the final user turn, grounded in the analysis + question evidence."""
    question = (messages[-1].get('content') or '').strip()
    history = messages[:-1]
    analysis_dict = plant_service.serialize_analysis(analysis)
    context = retrieve_for_question(db, analysis, question)

    mode = 'KG-grounded chat (deterministic fallback)'
    answer_text = None
    if llm_service.is_configured():
        answer_text = llm_service.chat(analysis=analysis_dict, evidence=context,
                                       history=history, question=question)
        if answer_text:
            mode = f"LLM-grounded chat ({llm_service.model_name()})"

    if answer_text:
        sources: list[dict] = []
        for t in context['triples'][:3]:
            _add_source(sources, 'Knowledge graph', _triple_line(t))
        for d in context['documents'][:2]:
            _add_source(sources, 'Document', d['title'])
    else:
        answer_text, sources = _fallback_answer(analysis_dict, context, question)

    return {'answer': answer_text, 'sources': sources[:6], 'mode': mode}