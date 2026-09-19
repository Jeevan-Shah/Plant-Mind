import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Search } from 'lucide-react';
import { api } from '../lib/api';
import type { Entity } from '../types';
import { Badge, Card, EmptyState, Spinner, inputClass } from '../components/ui';

const TYPE_TABS = ['All', 'Plant', 'Disease', 'Symptom', 'EnvironmentalCondition', 'Treatment'];
const TAB_LABEL: Record<string, string> = {
  All: 'All', Plant: 'Plants', Disease: 'Diseases', Symptom: 'Symptoms',
  EnvironmentalCondition: 'Conditions', Treatment: 'Treatments',
};

const TYPE_TONE: Record<string, string> = {
  Plant: 'green', Disease: 'red', Symptom: 'amber',
  EnvironmentalCondition: 'blue', Treatment: 'slate',
};

export function KnowledgeExplorer() {
  const [q, setQ] = useState('');
  const [tab, setTab] = useState('All');
  const [selected, setSelected] = useState<Entity | null>(null);

  const entities = useQuery({
    queryKey: ['knowledge', q, tab],
    queryFn: () => api.searchKnowledge(q, tab === 'All' ? undefined : tab),
  });
  const rels = useQuery({
    queryKey: ['knowledge-rel', selected?.id],
    queryFn: () => api.knowledgeRelationships(selected!.id),
    enabled: Boolean(selected),
  });
  const types = useQuery({ queryKey: ['knowledge-types'], queryFn: api.knowledgeTypes });

  const Triple = ({ s, r, t, tone }: { s: string; r: string; t: string; tone: string }) => (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2 text-xs">
      <span className="font-medium text-slate-700">{s}</span>
      <ArrowRight className="h-3 w-3 text-slate-400" />
      <span className="font-mono text-[11px] text-slate-500">{r}</span>
      <ArrowRight className="h-3 w-3 text-slate-400" />
      <span className="font-medium text-slate-700">{t}</span>
      <Badge tone={tone}>{r}</Badge>
    </div>
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Knowledge Explorer</h1>
        <p className="mt-0.5 text-sm text-slate-500">
          The plant-care knowledge graph powering PlantMind's evidence retrieval. V1 demonstration base.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {TYPE_TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition ${
              tab === t ? 'bg-brand-600 text-white' : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}`}>
            {TAB_LABEL[t]}
            {types.data && t !== 'All' && (
              <span className="ml-1.5 opacity-60">{types.data[t] ?? 0}</span>
            )}
          </button>
        ))}
        <div className="relative ml-auto">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input className={`${inputClass} w-64 pl-9`} placeholder="Search knowledge…" value={q}
            onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Entities" subtitle={selected ? 'Select another entity to explore it' : 'Select an entity to see its relationships'}>
          {entities.isLoading ? <Spinner /> : (
            (entities.data ?? []).length === 0 ? (
              <EmptyState title="No matches" subtitle="Try a different search term or tab." />
            ) : (
              <div className="max-h-[480px] space-y-2 overflow-y-auto pr-1">
                {(entities.data ?? []).map((e) => (
                  <button key={e.id} onClick={() => setSelected(e)}
                    className={`block w-full rounded-xl border p-3 text-left transition ${
                      selected?.id === e.id ? 'border-brand-300 bg-brand-50/60' : 'border-slate-100 hover:border-brand-200'}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-slate-800">{e.name}</span>
                      <Badge tone={TYPE_TONE[e.entity_type] ?? 'slate'}>{e.entity_type}</Badge>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500">{e.description}</p>
                  </button>
                ))}
              </div>
            )
          )}
        </Card>

        <Card title="Relationships" subtitle={selected ? `${selected.name} — connected knowledge` : 'Pick an entity on the left'}>
          {!selected ? (
            <EmptyState title="No entity selected"
              subtitle="Example: select Tomato, then follow susceptibleTo → Early Blight → managedBy → treatments." />
          ) : rels.isLoading || !rels.data ? <Spinner /> : (
            <div className="max-h-[480px] space-y-3 overflow-y-auto pr-1">
              <div className="rounded-xl bg-brand-50 p-3">
                <p className="text-sm font-semibold text-brand-900">{selected.name}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-brand-700/80">{selected.description}</p>
              </div>
              {(['outgoing', 'incoming'] as const).map((dir) => (
                <div key={dir}>
                  <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">{dir}</p>
                  <div className="space-y-2">
                    {(rels.data![dir] ?? []).map((t, i) => (
                      <Triple key={i} s={t.source_name} r={t.relationship} t={t.target_name}
                        tone={TYPE_TONE[t.target_type] ?? 'slate'} />
                    ))}
                    {(rels.data![dir] ?? []).length === 0 && (
                      <p className="text-xs text-slate-400">None.</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
