import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ArrowLeft, Pencil, Trash2 } from 'lucide-react';
import { api, imageUrl } from '../lib/api';
import { Badge, Button, Card, EmptyState, ErrorState, Spinner, formatDateTime, healthTone, riskTone } from '../components/ui';
import { navigate } from '../hooks/useRoute';
import { PlantModal } from '../components/PlantModal';
import { CompactAnalysisRow } from '../components/AnalysisReport';

export function PlantDetails({ plantId }: { plantId: number }) {
  const qc = useQueryClient();
  const plant = useQuery({ queryKey: ['plant', plantId], queryFn: () => api.getPlant(plantId) });
  const analyses = useQuery({ queryKey: ['analyses', plantId], queryFn: () => api.plantAnalyses(plantId) });
  const care = useQuery({ queryKey: ['care', plantId], queryFn: () => api.plantCare(plantId) });
  const [editOpen, setEditOpen] = useState(false);

  const del = useMutation({
    mutationFn: () => api.deletePlant(plantId),
    onSuccess: () => { toast.success('Plant deleted.'); navigate('/plants'); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (plant.isLoading) return <Spinner label="Loading plant…" />;
  if (plant.isError) return <ErrorState message={(plant.error as Error).message} />;
  const p = plant.data!;
  const latest = analyses.data?.[0];
  const state = latest?.plant_state ?? {};

  return (
    <div className="space-y-5">
      <button onClick={() => navigate('/plants')}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> All plants
      </button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          {p.image_path
            ? <img src={imageUrl(p.image_path)!} alt={p.name} className="h-16 w-16 rounded-2xl object-cover" />
            : <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-3xl">🌱</div>}
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{p.name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <Badge tone="slate">{p.species}</Badge>
              <Badge tone="blue">{p.growth_stage}</Badge>
              <Badge tone={healthTone(p.health_status)}>{p.health_status}</Badge>
              {state.risk_level && <Badge tone={riskTone(state.risk_level)}>{String(state.risk_level)} risk</Badge>}
              {p.is_demo && <Badge tone="amber">demo data</Badge>}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setEditOpen(true)}><Pencil className="h-4 w-4" /> Edit</Button>
          <Button variant="danger" onClick={() => { if (window.confirm(`Delete "${p.name}"?`)) del.mutate(); }}>
            <Trash2 className="h-4 w-4" /> Delete
          </Button>
          <Button onClick={() => navigate(`/analyze/${p.id}`)}>Analyze Plant</Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Plant profile" className="lg:col-span-1">
          <dl className="space-y-2.5 text-sm">
            {[
              ['Species', p.species], ['Growth stage', p.growth_stage], ['Age', `${p.age_days} days`],
              ['Watering', p.watering_frequency], ['Light', p.light_condition], ['Notes', p.notes || '—'],
            ].map(([k, v]) => (
              <div key={k} className="grid grid-cols-[110px_1fr] gap-2">
                <dt className="text-slate-400">{k}</dt>
                <dd className="text-slate-700">{v}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card title="Latest analysis" className="lg:col-span-2">
          {!latest ? (
            <EmptyState title="Not analyzed yet"
              subtitle="Run an analysis with a leaf photo to see the condition, reasoning and evidence here."
              action={<Button onClick={() => navigate(`/analyze/${p.id}`)}>Analyze Plant</Button>} />
          ) : (
            <div>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-lg font-semibold text-slate-900">{latest.predicted_condition}</p>
                  <p className="text-xs text-slate-400">{formatDateTime(latest.created_at)}</p>
                </div>
                <div className="flex gap-2">
                  <Badge tone="blue">{Math.round(latest.confidence * 100)}% (demo)</Badge>
                  <Button variant="secondary" onClick={() => navigate(`/analysis/${latest.id}`)}>View full report</Button>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {latest.detected_symptoms.map((s) => <Badge key={s} tone="amber">{s}</Badge>)}
              </div>
            </div>
          )}
        </Card>

        <Card title="Care history" className="lg:col-span-1">
          {(care.data ?? []).length === 0 ? (
            <p className="text-sm text-slate-400">No care events recorded yet.</p>
          ) : (
            <ol className="space-y-2.5">
              {(care.data ?? []).slice(0, 8).map((c) => (
                <li key={c.id} className="border-l-2 border-brand-200 pl-3">
                  <p className="text-xs font-medium text-brand-700">{c.event_type}</p>
                  <p className="text-sm text-slate-600">{c.description}</p>
                  <p className="text-[11px] text-slate-400">{formatDateTime(c.date)}</p>
                </li>
              ))}
            </ol>
          )}
        </Card>

        <Card title="Previous analyses" subtitle="Analysis timeline for progression tracking" className="lg:col-span-2">
          {(analyses.data ?? []).length === 0 ? (
            <p className="text-sm text-slate-400">Analyses will appear here as a timeline.</p>
          ) : (
            <div className="space-y-2">
              {(analyses.data ?? []).map((a) => (
                <button key={a.id} onClick={() => navigate(`/analysis/${a.id}`)} className="block w-full text-left">
                  <CompactAnalysisRow analysis={a} />
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      <PlantModal open={editOpen} onOpenChange={setEditOpen} plant={p}
        onSaved={() => qc.invalidateQueries({ queryKey: ['plant', plantId] })} />
    </div>
  );
}

