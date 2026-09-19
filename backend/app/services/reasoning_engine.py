"""Deterministic knowledge-graph reasoning engine — the local fallback brain.

When no LLM API key is configured, this module produces the diagnosis,
explanation, evidence, recommendations and preventive care using ONLY the
plant state and the retrieved knowledge-graph evidence. Output is labelled
"Knowledge-based demo reasoning" so demo mode is never presented as a
hosted-LLM answer.
"""
from __future__ import annotations

REASONING_MODE = 'Knowledge-based demo reasoning (no external LLM configured)'


def diagnose(plant_state: dict, graph_context: dict) -> dict:
    """Score diseases in the evidence by symptom/species/condition overlap."""
    species = (plant_state.get('species') or '').strip().lower()
    symptoms = {s.lower() for s in plant_state.get('symptoms', [])}
    reported = (plant_state.get('reported_symptoms_text') or '').lower()
    env_flags = ' '.join(plant_state.get('environmental_flags', [])).lower()
    profile_text = f"{plant_state.get('watering_frequency', '')} {plant_state.get('light_condition', '')}".lower()

    # Candidate diseases mentioned anywhere in the retrieved triples.
    candidates: dict[str, float] = {}
    details: dict[str, dict] = {}
    for t in graph_context.get('triples', []):
        src, rel, tgt = t['source'], t['relationship'], t['target']
        if src.startswith('disease_') and rel == 'hasSymptom' and tgt.startswith('symptom_'):
            c = candidates.setdefault(src, 0.0)
            d = details.setdefault(src, {'symptom_hits': []})
            if tgt.replace('symptom_', '').replace('_', ' ') in symptoms or \
               t['target_name'].lower() in reported:
                candidates[src] = c + 2.0
                d['symptom_hits'].append(t['target_name'])
        if tgt.startswith('disease_') and rel in ('susceptibleTo',) and src.startswith('plant_'):
            if src.replace('plant_', '') == species or t['source_name'].lower() == species:
                candidates[tgt] = candidates.get(tgt, 0.0) + 1.5
                d = details.setdefault(tgt, {'symptom_hits': []})
                d['species_susceptible'] = True
        if tgt.startswith('disease_') and rel in ('favors', 'causes'):
            flag_hit = ('humidity' in env_flags and 'humidity' in t['source_name'].lower()) or \
                       ('moisture' in env_flags and 'moisture' in t['source_name'].lower()) or \
                       ('moisture' in profile_text and 'moisture' in t['source_name'].lower())
            if flag_hit:
                candidates[tgt] = candidates.get(tgt, 0.0) + 0.8

    ranked = sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)
    top_id, top_score = (ranked[0] if ranked else (None, 0.0))
    if top_score < 2.0:
        return {'condition': 'Inconclusive — insufficient evidence',
                'condition_id': None, 'confidence': 0.35,
                'runners_up': [], 'matched_symptoms': []}

    # Demo confidence: bounded, derived from evidence strength, NOT accuracy.
    matched = details[top_id].get('symptom_hits', [])
    susceptible = details[top_id].get('species_susceptible', False)
    confidence = round(min(0.9, 0.45 + 0.15 * len(matched) + (0.1 if susceptible else 0.0)), 2)
    runners = [{'condition': rid.replace('disease_', '').replace('_', ' ').title(),
                'score': s} for rid, s in ranked[1:3]]
    return {
        'condition': top_id.replace('disease_', '').replace('_', ' ').title(),
        'condition_id': top_id,
        'confidence': confidence,
        'runners_up': runners,
        'matched_symptoms': matched,
        'species_susceptible': susceptible,
    }


def build_explanation(plant_state: dict, diagnosis: dict) -> list[str]:
    steps: list[str] = []
    if plant_state.get('symptoms'):
        steps.append(f"Symptoms detected in the image analysis: "
                     f"{', '.join(plant_state['symptoms'])}.")
    if plant_state.get('reported_symptoms_text'):
        steps.append(f"Symptoms reported by you: \"{plant_state['reported_symptoms_text']}\".")
    if diagnosis.get('matched_symptoms'):
        steps.append(f"These symptoms match the knowledge-graph symptom links of "
                     f"{diagnosis['condition']}: {', '.join(diagnosis['matched_symptoms'])}.")
    if diagnosis.get('species_susceptible'):
        steps.append(f"The knowledge graph marks {plant_state.get('species')} as "
                     f"susceptible to {diagnosis['condition']}, which supports this hypothesis.")
    flags = plant_state.get('environmental_flags', [])
    if flags:
        steps.append("Plant profile context: " + '; '.join(flags) + ".")
    stage = plant_state.get('growth_stage')
    if stage in ('Flowering', 'Fruiting'):
        steps.append(f"The plant is in the {stage} stage, so it has higher resource demands; "
                     "stress may intensify symptoms.")
    if not steps:
        steps.append("No strong symptom signals were found; the result is inconclusive.")
    steps.append("Reasoning used only the retrieved knowledge-graph evidence and the plant state.")
    return steps


def build_recommendations(plant_state: dict, diagnosis: dict,
                          graph_context: dict) -> list[dict]:
    """Recommendations generated from managedBy evidence + plant personalization."""
    recs: list[dict] = []
    seen_titles: set[str] = set()

    def add(title: str, why: str, source: str, priority: str = 'Important') -> None:
        if title.lower() in seen_titles:
            return
        seen_titles.add(title.lower())
        recs.append({'title': title, 'why': why, 'source': source, 'priority': priority})

    if diagnosis.get('condition_id'):
        for t in graph_context.get('triples', []):
            if t['source'] == diagnosis['condition_id'] and t['relationship'] == 'managedBy':
                add(t['target_name'],
                    f"Knowledge graph: {diagnosis['condition']} is managed by this action.",
                    f"{diagnosis['condition']} → managedBy → {t['target_name']}")

    # --- Personalization from the plant profile & history (demo heuristics) ---
    watering = (plant_state.get('watering_frequency') or '').lower()
    if any(w in watering for w in ('daily', 'every day', 'twice')):
        add('Re-check your watering schedule',
            f"You water \"{plant_state.get('watering_frequency')}\"; combined with the current "
            "symptoms this can keep foliage/soil too wet.",
            'Plant profile personalization')
    light = (plant_state.get('light_condition') or '').lower()
    if any(w in light for w in ('low', 'shade')):
        add('Move the plant to a brighter location',
            f"Current light condition is \"{plant_state.get('light_condition')}\"; "
            "more light supports recovery and drier foliage.",
            'Plant profile personalization')
    stage = plant_state.get('growth_stage')
    if stage in ('Flowering', 'Fruiting'):
        add(f'Support the plant during the {stage.lower()} stage',
            "Flowering/fruiting plants divert energy to reproduction; "
            "avoid extra stress while treating symptoms.",
            'Plant profile personalization')
    age = plant_state.get('age_days')
    if isinstance(age, int) and age <= 21:
        add('Handle the young plant gently',
            f"At {age} days old the plant is fragile; prefer the least invasive actions first.",
            'Plant profile personalization')

    if not recs:
        add('Monitor the plant and re-analyse in a few days',
            'No condition-specific actions were found in the knowledge base for this evidence.',
            'Fallback guidance')
    return recs[:6]


def build_preventive_care(diagnosis: dict, graph_context: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    if diagnosis.get('condition_id'):
        for t in graph_context.get('triples', []):
            if t['source'] == diagnosis['condition_id'] and t['relationship'] == 'preventedBy':
                key = t['target_name'].lower()
                if key not in seen:
                    seen.add(key)
                    items.append({'title': t['target_name'],
                                  'source': f"{t['source_name']} → preventedBy → {t['target_name']}"})
    generic = [
        {'title': 'Inspect leaves (top and underside) weekly',
         'source': 'General preventive care knowledge'},
        {'title': 'Water at the base and keep foliage dry',
         'source': 'General preventive care knowledge'},
        {'title': 'Keep adequate spacing for airflow around the plant',
         'source': 'General preventive care knowledge'},
    ]
    for g in generic:
        if g['title'].lower() not in seen:
            items.append(g)
    return items[:5]


def build_limitations() -> list[str]:
    return [
        'Vision analysis uses the Demo Vision Model (heuristic colour analysis), '
        'not a trained disease classifier.',
        'Confidence is a demo value derived from evidence strength; it is not a measured model accuracy.',
        'The knowledge graph is a small demonstration knowledge base and is not scientifically exhaustive.',
        'This is a possible diagnosis, not a confirmed diagnosis; verify with reliable '
        'agricultural sources or experts.',
    ]
