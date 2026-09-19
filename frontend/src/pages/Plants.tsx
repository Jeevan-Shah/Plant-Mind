import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { api, imageUrl } from '../lib/api';
import type { Plant } from '../types';
import { Badge, Button, Card, EmptyState, ErrorState, Spinner, formatDateTime, healthTone } from '../components/ui';
import { navigate } from '../hooks/useRoute';
import { PlantModal } from '../components/PlantModal';

export function Plants() {
  const qc = useQueryClient();
  const plants = useQuery({ queryKey: ['plants'], queryFn: api.listPlants });
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Plant | null>(null);

  const del = useMutation({
    mutationFn: (id: number) => api.deletePlant(id),
    onSuccess: () => { toast.success('Plant deleted.'); qc.invalidateQueries({ queryKey: ['plants'] }); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (plants.isLoading) return <Spinner label="Loading plants…" />;
  if (plants.isError) return <ErrorState message={(plants.error as Error).message} />;
  const list = plants.data ?? [];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Plants</h1>
          <p className="mt-0.5 text-sm text-slate-500">Your personal plant registry.</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true); }}>
          <Plus className="h-4 w-4" /> Add Plant
        </Button>
      </div>

      {list.length === 0 ? (
        <EmptyState title="No plants yet" subtitle="Add a plant, then analyze it with a leaf photo and observed symptoms."
          action={<Button onClick={() => setModalOpen(true)}><Plus className="h-4 w-4" /> Add Plant</Button>} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                <th className="pb-3 pr-4 font-medium">Plant</th>
                <th className="pb-3 pr-4 font-medium">Species</th>
                <th className="pb-3 pr-4 font-medium">Growth stage</th>
                <th className="pb-3 pr-4 font-medium">Health</th>
                <th className="pb-3 pr-4 font-medium">Last analysis</th>
                <th className="pb-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {list.map((p) => (
                <tr key={p.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="py-3 pr-4">
                    <button onClick={() => navigate(`/plants/${p.id}`)} className="flex items-center gap-3 text-left">
                      {p.image_path
                        ? <img src={imageUrl(p.image_path)!} alt="" className="h-9 w-9 rounded-lg object-cover" />
                        : <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50">🌱</span>}
                      <span>
                        <span className="block font-medium text-slate-800">{p.name}</span>
                        <span className="block text-xs text-slate-400">{p.analysis_count} analysis(es)</span>
                      </span>
                    </button>
                  </td>
                  <td className="py-3 pr-4 text-slate-600">{p.species}</td>
                  <td className="py-3 pr-4 text-slate-600">{p.growth_stage}</td>
                  <td className="py-3 pr-4"><Badge tone={healthTone(p.health_status)}>{p.health_status}</Badge></td>
                  <td className="py-3 pr-4 text-xs text-slate-500">
                    {formatDateTime(p.last_analysis)}
                    {p.latest_condition && <span className="block text-slate-400">{p.latest_condition}</span>}
                  </td>
                  <td className="py-3">
                    <div className="flex gap-1">
                      <button title="View" onClick={() => navigate(`/plants/${p.id}`)}
                        className="rounded-lg p-2 text-slate-400 hover:bg-brand-50 hover:text-brand-700">View</button>
                      <button title="Edit" onClick={() => { setEditing(p); setModalOpen(true); }}
                        className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button title="Delete" onClick={() => {
                        if (window.confirm(`Delete "${p.name}" and all of its analyses?`)) del.mutate(p.id);
                      }} className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <PlantModal open={modalOpen} onOpenChange={setModalOpen} plant={editing}
        onSaved={() => qc.invalidateQueries({ queryKey: ['plants'] })} />
    </div>
  );
}
