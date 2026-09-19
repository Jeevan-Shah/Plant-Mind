import { ArrowRight, BookOpen, CheckCircle2, FlaskConical, Lightbulb, Network, ShieldAlert, ShieldCheck } from 'lucide-react';
import type { Analysis, Triple } from '../types';
import { Badge, Card, riskTone } from './ui';
import { formatDateTime, pct } from './ui';

function TripleRow({ t }: { t: Triple }) {
  const color = t.source_type === 'Plant' ? 'bg-brand-100 text-brand-800'
    : t.source_type === 'Disease' ? 'bg-red-100 text-red-700'
    : t.source_type === 'Symptom' ? 'bg-amber-100 text-amber-800'
    : t.target_type === 'Treatment' ? 'bg-sky-100 text-sky-800'
    : 'bg-slate-100 text-slate-600';
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2 text-xs">
      <span className={`rounded-md px-2 py-0.5 font-medium ${color}`}>{t.source_name}</span>
      <ArrowRight className="h-3 w-3 text-slate-400" />
      <span className="font-mono text-[11px] text-slate-500">{t.relationship}</span>
      <ArrowRight className="h-3 w-3 text-slate-400" />
      <span className={`rounded-md px-2 py-0.5 font-medium ${color}`}>{t.target_name}</span>
    </div>
  );
}

export function AnalysisReport({ analysis }: { analysis: Analysis }) {
  const state = analysis.plant_state ?? {};
  const triples = (analysis.evidence?.triples ?? []).slice(0, 12);
  const entities = analysis.evidence?.identified_entities ?? [];
  const docs = analysis.evidence?.documents ?? [];

  return (
    <div className="space-y-4">
      {/* Condition header */}
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Possible condition</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-900">{analysis.predicted_condition}</h2>
            <p className="mt-1 text-xs text-slate-400">Analyzed {formatDateTime(analysis.created_at)}</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Confidence</span>
              <Badge tone="blue">{pct(analysis.confidence)} (demo value)</Badge>
            </div>
            {state.risk_level && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Plant state risk</span>
                <Badge tone={riskTone(state.risk_level)}>{String(state.risk_level)} Risk</Badge>
              </div>
            )}
            {analysis.is_demo && (
              <Badge tone="amber"><FlaskConical className="h-3 w-3" /> Demo Vision Model</Badge>
            )}
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-xs font-medium text-slate-500">Observed symptoms</p>
            <ul className="mt-2 space-y-1">
              {analysis.detected_symptoms.length
                ? analysis.detected_symptoms.map((s) => (
                    <li key={s} className="flex items-center gap-2 text-sm text-slate-700">
                      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> {s}
                    </li>
                  ))
                : <li className="text-sm text-slate-400">No distinct symptoms detected</li>}
            </ul>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-xs font-medium text-slate-500">Plant state</p>
            <div className="mt-2 grid grid-cols-2 gap-y-1.5 text-sm">
              <span className="text-slate-400">Species</span><span>{String(state.species ?? '—')}</span>
              <span className="text-slate-400">Growth stage</span><span>{String(state.growth_stage ?? '—')}</span>
              <span className="text-slate-400">Age</span><span>{String(state.age_days ?? '—')} days</span>
              <span className="text-slate-400">Risk</span><span>{String(state.risk_level ?? '—')}</span>
            </div>
          </div>
        </div>
        {analysis.llm_summary && (
          <div className="mt-4 rounded-xl border border-sky-100 bg-sky-50/60 p-4 text-sm leading-relaxed text-slate-700">
            {analysis.llm_summary}
          </div>
        )}
        <p className="mt-3 text-[11px] text-slate-400">Reasoning mode: {analysis.reasoning_mode}</p>
      </Card>

      {/* Why */}
      <Card title="Why this result?" subtitle="Explainable reasoning derived from the plant state and retrieved knowledge">
        <ol className="space-y-2.5">
          {analysis.explanation.map((step, i) => (
            <li key={i} className="flex gap-3 text-sm text-slate-700">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[11px] font-semibold text-brand-700">{i + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </Card>

      {/* Evidence */}
      <Card title="Evidence" subtitle="Retrieved knowledge-graph relationships and supporting knowledge">
        {entities.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {entities.map((e) => (
              <span key={e.entity_id} title={e.match_reason}
                className="rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800">
                <Network className="mr-1 inline h-3 w-3" />{e.name}
                <span className="ml-1 font-normal text-brand-600">· {e.entity_type}</span>
              </span>
            ))}
          </div>
        )}
        <div className="grid gap-2 md:grid-cols-2">
          {triples.map((t, i) => <TripleRow key={i} t={t} />)}
        </div>
        {docs.length > 0 && (
          <div className="mt-4 space-y-2">
            {docs.map((d) => (
              <div key={d.title} className="rounded-xl border border-slate-100 p-3">
                <p className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                  <BookOpen className="h-3.5 w-3.5 text-slate-400" /> {d.title}
                </p>
                <p className="mt-1 whitespace-pre-line text-xs leading-relaxed text-slate-500">{d.excerpt}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Recommendations */}
      <Card title="Recommended actions" subtitle="Generated from retrieved knowledge and this plant's profile">
        <ol className="space-y-3">
          {analysis.recommendation.map((r, i) => (
            <li key={i} className="flex gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-brand-600 text-xs font-semibold text-white">{i + 1}</span>
              <div>
                <p className="flex items-center gap-2 text-sm font-medium text-slate-800">
                  <Lightbulb className="h-3.5 w-3.5 text-amber-400" /> {r.title}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">{r.why}</p>
                <p className="mt-1 font-mono text-[10px] text-slate-400">source: {r.source}</p>
              </div>
            </li>
          ))}
        </ol>
      </Card>

      {/* Preventive care */}
      <Card title="Preventive care">
        <ul className="space-y-2">
          {analysis.preventive_care.map((p, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />
              <div>
                {p.title}
                <span className="ml-2 text-[10px] text-slate-400">{p.source}</span>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      {/* Limitations */}
      <Card title="Confidence & limitations" subtitle="Please read before acting on this advice">
        <ul className="space-y-2">
          {analysis.limitations.map((l, i) => (
            <li key={i} className="flex items-start gap-2.5 text-xs leading-relaxed text-slate-500">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" /> {l}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

export function CompactAnalysisRow({ analysis }: { analysis: Analysis }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-100 p-3">
      <CheckCircle2 className="h-4 w-4 shrink-0 text-brand-500" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-800">{analysis.predicted_condition}</p>
        <p className="text-xs text-slate-400">
          {formatDateTime(analysis.created_at)} · {analysis.detected_symptoms.length} symptom(s)
        </p>
      </div>
      <Badge tone="blue">{pct(analysis.confidence)}</Badge>
    </div>
  );
}
