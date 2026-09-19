import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { ErrorState, Spinner } from '../components/ui';
import { navigate } from '../hooks/useRoute';
import { AnalysisReport } from '../components/AnalysisReport';

export function AnalysisReportPage({ analysisId }: { analysisId: number }) {
  const analysis = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => api.getAnalysis(analysisId),
  });

  return (
    <div className="space-y-4">
      <button onClick={() => window.history.back()}
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back
      </button>
      {analysis.isLoading && <Spinner label="Loading report…" />}
      {analysis.isError && <ErrorState message={(analysis.error as Error).message} />}
      {analysis.data && (
        <>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            Plant Health Analysis — {analysis.data.plant_name}
          </h1>
          <AnalysisReport analysis={analysis.data} />
        </>
      )}
    </div>
  );
}
