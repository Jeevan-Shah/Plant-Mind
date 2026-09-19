import { useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, ChevronRight, Plus, Sprout } from 'lucide-react';
import { api, imageUrl } from '../lib/api';
import { Badge, Card, EmptyState, ErrorState, Spinner, StatCard, formatDateTime, healthTone, pct } from '../components/ui';
import { navigate } from '../hooks/useRoute';
import { PlantModal } from '../components/PlantModal';
import { useState } from 'react';

export function Dashboard() {
  const stats = useQuery({ queryKey: ['dashboard'], queryFn: api.dashboardStats });
  const plants = useQuery({ queryKey: ['plants'], queryFn: api.listPlants });
  const [modalOpen, setModalOpen] = useState(false);

  if (stats.isLoading || plants.isLoading) return <Spinner label="Loading dashboard…" />;
  if (stats.isError) return <ErrorState message={(stats.error as Error).message} />;
  const s = stats.data!;
  const recentPlants = (plants.data ?? []).slice(0, 4);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            Your Intelligent Plant-Care Assistant
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Image + plant profile + care history → Plant State → Knowledge Graph → GraphRAG → explainable guidance.
          </p>
        </div>
        <button onClick={() => navigate('/analyze')}
          className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-brand-700">
          <Activity className="h-4 w-4" /> Analyze Plant
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Plants" value={s.total_plants} icon={<Sprout className="h-5 w-5" />} accent />
        <StatCard label="Analyses" value={s.total_analyses} icon={<Activity className="h-5 w-5" />} />
        <StatCard label="Needs Attention" value={s.needs_attention} hint={`${s.monitor} to monitor · ${s.new_plants} new`}
          icon={<AlertTriangle className="h-5 w-5" />} />
        <StatCard label="Healthy" value={s.healthy} hint="Latest analysis shows no issue"
          icon={<span className="text-lg">🌿</span>} />
      </div>

      <Card title="Recent plants"
        actions={<button onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:text-brand-800">
          <Plus className="h-3.5 w-3.5" /> Add plant</button>}>
        {recentPlants.length === 0 ? (
          <EmptyState title="No plants yet" subtitle="Add your first plant to start tracking its health."
            action={<button onClick={() => setModalOpen(true)}
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white">Add Plant</button>} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {recentPlants.map((p) => (
              <button key={p.id} onClick={() => navigate(`/plants/${p.id}`)}
                className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 text-left transition hover:border-brand-200 hover:bg-brand-50/40">
                {p.image_path
                  ? <img src={imageUrl(p.image_path)!} alt={p.name} className="h-11 w-11 rounded-lg object-cover" />
                  : <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-brand-50 text-lg">🌱</div>}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-800">{p.name}</p>
                  <p className="text-xs text-slate-400">{p.species} · {p.growth_stage}</p>
                </div>
                <Badge tone={healthTone(p.health_status)}>{p.health_status}</Badge>
                <ChevronRight className="h-4 w-4 text-slate-300" />
              </button>
            ))}
          </div>
        )}
      </Card>

      <Card title="Recent analyses">
        {s.recent_conditions.length === 0 ? (
          <EmptyState title="No analyses yet"
            subtitle="Run your first plant analysis to see explainable results here."
            action={<button onClick={() => navigate('/analyze')}
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white">Analyze Plant</button>} />
        ) : (
          <div className="space-y-2">
            {s.recent_conditions.map((c) => (
              <button key={c.analysis_id} onClick={() => navigate(`/plants/${c.plant_id}`)}
                className="flex w-full flex-wrap items-center gap-3 rounded-xl border border-slate-100 p-3 text-left hover:border-brand-200">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-800">{c.plant_name}</p>
                  <p className="text-xs text-slate-400">{formatDateTime(c.created_at)}</p>
                </div>
                <span className="text-sm text-slate-600">{c.condition}</span>
                {c.risk_level && <Badge tone={c.risk_level === 'High' ? 'red' : c.risk_level === 'Moderate' ? 'amber' : 'green'}>{c.risk_level} risk</Badge>}
                <Badge tone="blue">{pct(c.confidence)}</Badge>
              </button>
            ))}
          </div>
        )}
      </Card>

      <PlantModal open={modalOpen} onOpenChange={setModalOpen} plant={null}
        onSaved={() => { stats.refetch(); plants.refetch(); }} />
    </div>
  );
}
