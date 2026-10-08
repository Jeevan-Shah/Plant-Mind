"""LLM service — modular provider with a local deterministic fallback.

If LLM_API_KEY is set, an OpenAI-compatible chat-completions endpoint is used.
The prompt is strictly grounded: the model receives the plant state and the
retrieved evidence and is instructed to use ONLY that evidence. If no key is
configured (or the API call fails), the caller falls back to the deterministic
knowledge-graph reasoning engine.
"""
from __future__ import annotations

import httpx

from ..config import (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
                      LLM_TIMEOUT_SECONDS)

SYSTEM_PROMPT = """You are a plant-care decision support assistant.
Use ONLY the retrieved evidence and plant state.
Clearly distinguish possible diagnosis from confirmed diagnosis.
Explain the reasoning.
Do not invent evidence.
Give practical recommendations.
If evidence is insufficient, say so.
"""


def is_configured() -> bool:
    return bool(LLM_API_KEY)


def model_name() -> str:
    return LLM_MODEL


def _build_user_prompt(plant_state: dict, evidence: dict, diagnosis: dict) -> str:
    triples = '\n'.join(
        f"- {t['source_name']} --[{t['relationship']}]--> {t['target_name']}"
        for t in evidence.get('triples', [])[:40])
    docs = '\n\n'.join(
        f"Document: {d['title']}\n{d['excerpt']}" for d in evidence.get('documents', []))
    return (
        f"PLANT STATE:\n{plant_state}\n\n"
        f"RETRIEVED KNOWLEDGE-GRAPH EVIDENCE (use only this):\n{triples or '(none)'}\n\n"
        f"RETRIEVED DOCUMENTS:\n{docs or '(none)'}\n\n"
        f"PRELIMINARY KG-BASED DIAGNOSIS: {diagnosis.get('condition')} "
        f"(demo confidence {diagnosis.get('confidence')})\n\n"
        "Task: In 4-6 sentences, explain why this possible condition fits this specific plant, "
        "what the user should do next, and what remains uncertain. "
        "Clearly state it is a POSSIBLE diagnosis, not a confirmed one. "
        "Then on the last line output 'EXTRA: ' followed by up to 3 short, practical "
        "action suggestions separated by ';' that are consistent with the evidence."
    )


def generate(plant_state: dict, evidence: dict, diagnosis: dict) -> dict | None:
    """Call the configured LLM. Returns None on any failure (caller falls back)."""
    if not is_configured():
        return None
    payload = {
        'model': LLM_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': _build_user_prompt(plant_state, evidence, diagnosis)},
        ],
        'temperature': 0.2,
        'max_tokens': 500,
    }
    headers = {'Authorization': f'Bearer {LLM_API_KEY}'}
    try:
        response = httpx.post(f'{LLM_BASE_URL}/chat/completions', json=payload,
                              headers=headers, timeout=LLM_TIMEOUT_SECONDS)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
    except Exception:
        return None

    summary, _, extra = content.partition('EXTRA:')
    extra_recommendations = []
    for part in extra.replace('\n', ' ').split(';'):
        part = part.strip(' -•0123456789.')
        if part:
            extra_recommendations.append(part)
    return {'summary': summary.strip(), 'extra_recommendations': extra_recommendations[:3]}

# --- Follow-up chat -----------------------------------------------------------
CHAT_SYSTEM_PROMPT = """You are PlantMind's plant-care follow-up assistant inside an explainable plant-health app.
You help the user understand ONE completed analysis. Answer ONLY from the ANALYSIS
CONTEXT and RETRIEVED EVIDENCE provided in this message - do not use outside facts.
Rules:
- Be concise (max 120 words), friendly and practical.
- Say plainly when the evidence does not cover the question instead of inventing facts.
- Keep calling the diagnosis a POSSIBLE condition unless evidence confirms it.
- End with one short concrete next step when applicable.
"""


def _analysis_block(analysis: dict) -> str:
    state = analysis.get('plant_state') or {}
    recs = '; '.join(r.get('title', '') for r in (analysis.get('recommendation') or [])[:5])
    return (
        f"Plant: {analysis.get('plant_name')} ({state.get('species')}), "
        f"stage {state.get('growth_stage')}, age {state.get('age_days')} days\n"
        f"Possible condition: {analysis.get('predicted_condition')} "
        f"(demo confidence {round((analysis.get('confidence') or 0) * 100)}%)\n"
        f"Plant-state risk: {state.get('risk_level')}\n"
        f"Detected symptoms: {', '.join(analysis.get('detected_symptoms') or []) or 'none'}\n"
        f"Reported by user: {state.get('reported_symptoms_text') or 'none'}\n"
        f"Watering: {state.get('watering_frequency')} | Light: {state.get('light_condition')}\n"
        f"Environmental flags: {', '.join(state.get('environmental_flags') or []) or 'none'}\n"
        f"Explanation: {' '.join((analysis.get('explanation') or [])[:3])}\n"
        f"Recommendations: {recs or 'none'}\n"
        f"Limitations: {' '.join((analysis.get('limitations') or [])[:2])}"
    )


def _evidence_block(evidence: dict) -> str:
    entities = ', '.join(f"{e['name']} ({e.get('entity_type', '?')})"
                         for e in evidence.get('entities', [])[:15])
    triples = '\n'.join(
        f"- {t['source_name']} ({t['relationship']}) {t['target_name']}"
        for t in evidence.get('triples', [])[:30])
    docs = '\n\n'.join(
        f"Document: {d['title']}\n{d['excerpt']}" for d in evidence.get('documents', []))
    return f"Entities: {entities or '(none)'}\n\nTriples:\n{triples or '(none)'}\n\nDocuments:\n{docs or '(none)'}"


def chat(analysis: dict, evidence: dict, history: list[dict],
         question: str) -> str | None:
    """Grounded follow-up answer. Returns None on any failure (caller falls back)."""
    if not is_configured():
        return None
    context = (f"ANALYSIS CONTEXT:\n{_analysis_block(analysis)}\n\n"
               f"RETRIEVED EVIDENCE (use only this):\n{_evidence_block(evidence)}")
    payload = {
        'model': LLM_MODEL,
        'messages': [
            {'role': 'system', 'content': CHAT_SYSTEM_PROMPT + '\n\n' + context},
            *[{'role': m['role'], 'content': m['content']} for m in history[-8:]],
            {'role': 'user', 'content': question},
        ],
        'temperature': 0.3,
        'max_tokens': 350,
    }
    headers = {'Authorization': f'Bearer {LLM_API_KEY}'}
    try:
        response = httpx.post(f'{LLM_BASE_URL}/chat/completions', json=payload,
                              headers=headers, timeout=LLM_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception:
        return None