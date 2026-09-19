import { useQuery } from '@tanstack/react-query';
import { api, imageUrl } from '../lib/api';
import { Badge, Card, EmptyState, ErrorState, Spinner, formatDateTime, riskTone } from '../components/ui';
import { navigate } from '../hooks/useRoute';

export function HistoryPage() {
  const analyses = useQuery({ queryKey: ['all-analyses'], queryFn: api.allAnalyses });

  if (analyses.isLoading) return <Spinner label="Loading analysis history…" />;
  if (analyses.isError) return <ErrorState message={(analyses.error as Error).message} />;
  const list = analyses.data ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Analysis History</h1>
        <p className="mt-0.5 text-sm text-slate-500">Every analysis is stored for progression tracking.</p>
      </div>

      {list.length === 0 ? (
        <EmptyState title="No analyses yet"
          subtitle="Analyses you run will appear here with their images and predicted conditions."
          action={<button onClick={() => navigate('/analyze')}
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white">Analyze Plant</button>} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                <th className="pb-3 pr-4 font-medium">Date</th>
                <th className="pb-3 pr-4 font-medium">Plant</th>
                <th className="pb-3 pr-4 font-medium">Image</th>
                <th className="pb-3 pr-4 font-medium">Predicted condition</th>
                <th className="pb-3 pr-4 font-medium">Confidence</th>
                <th className="pb-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {list.map((a) => (
                <tr key={a.id} onClick={() => navigate(`/analysis/${a.id}`)}
                  className="cursor-pointer border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="py-3 pr-4 text-xs text-slate-500">{formatDateTime(a.created_at)}</td>
                  <td className="py-3 pr-4 font-medium text-slate-800">{a.plant_name}</td>
                  <td className="py-3 pr-4">
                    {a.image_path
                      ? <img src={imageUrl(a.image_path)!} alt="" className="h-10 w-10 rounded-lg object-cover" />
                      : <span className="text-xs text-slate-300">—</span>}
                  </td>
                  <td className="py-3 pr-4 text-slate-700">{a.predicted_condition}</td>
                  <td className="py-3 pr-4"><Badge tone="blue">{Math.round(a.confidence * 100)}%</Badge></td>
                  <td className="py-3">
                    <Badge tone={riskTone(a.plant_state?.risk_level)}>
                      {a.plant_state?.risk_level ? `${a.plant_state.risk_level} risk` : '—'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
