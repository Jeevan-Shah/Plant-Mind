import { useCallback, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ImageUp, X, ScanSearch, Camera as CameraIcon } from 'lucide-react';
import { api } from '../lib/api';
import { takePhoto } from '../lib/camera';
import { Badge, Button, Card, ErrorState, Spinner, inputClass } from '../components/ui';
import { navigate } from '../hooks/useRoute';
import { AnalysisReport } from '../components/AnalysisReport';

const STEPS = [
  'Analyzing image (Demo Vision Model)…',
  'Building Plant State from profile & history…',
  'Retrieving knowledge-graph evidence (GraphRAG)…',
  'Generating explainable recommendation…',
];

export function AnalyzePage({ plantId }: { plantId?: number }) {
  const qc = useQueryClient();
  const plants = useQuery({ queryKey: ['plants'], queryFn: api.listPlants });
  const [selected, setSelected] = useState<number | undefined>(plantId);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [symptoms, setSymptoms] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [step, setStep] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFile = useCallback((f: File | undefined | null) => {
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast.error('Please choose an image file.'); return; }
    if (f.size > 8 * 1024 * 1024) { toast.error('Image must be under 8 MB.'); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const capture = useCallback(async () => {
    try {
      const f = await takePhoto();
      acceptFile(f);
    } catch {
      // User cancelled or denied permission — not an error worth a toast.
    }
  }, [acceptFile]);

  const analyze = useMutation({
    mutationFn: async () => {
      if (!selected || !file) throw new Error('Select a plant and upload an image first.');
      setStep(0);
      const timer = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 700);
      try {
        return await api.analyzePlant(selected, file, symptoms);
      } finally {
        clearInterval(timer);
        setStep(-1);
      }
    },
    onSuccess: () => {
      toast.success('Analysis complete.');
      qc.invalidateQueries({ queryKey: ['analyses'] });
      qc.invalidateQueries({ queryKey: ['plants'] });
    },
    onError: (e: Error) => { toast.error(e.message); setStep(-1); },
  });

  const result = analyze.data;
  const canAnalyze = Boolean(selected && file) && !analyze.isPending;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Plant Analysis</h1>
        <p className="mt-0.5 text-sm text-slate-500">
          Upload a leaf photo, describe symptoms, and let the knowledge-grounded pipeline explain what it finds.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Step 1 · Image & symptoms">
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Plant</label>
              <select className={inputClass} value={selected ?? ''}
                onChange={(e) => setSelected(e.target.value ? Number(e.target.value) : undefined)}>
                <option value="">Choose a plant…</option>
                {(plants.data ?? []).map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.species}, {p.growth_stage})</option>
                ))}
              </select>
              {(plants.data ?? []).length === 0 && !plants.isLoading && (
                <p className="mt-1 text-xs text-slate-400">No plants yet — add one on the Plants page first.</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Leaf / plant image</label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); acceptFile(e.dataTransfer.files[0]); }}
                onClick={() => inputRef.current?.click()}
                className={`flex min-h-48 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition ${
                  dragOver ? 'border-brand-400 bg-brand-50/60' : 'border-slate-300 bg-slate-50/50 hover:border-brand-300'}`}>
                {preview ? (
                  <div className="relative">
                    <img src={preview} alt="preview" className="max-h-56 rounded-xl object-contain" />
                    <button onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null); }}
                      className="absolute -right-2 -top-2 rounded-full bg-white p-1 shadow hover:bg-red-50">
                      <X className="h-4 w-4 text-red-500" />
                    </button>
                  </div>
                ) : (
                  <>
                    <ImageUp className="h-8 w-8 text-brand-500" />
                    <p className="mt-2 text-sm font-medium text-slate-600">Drag & drop an image, or click to browse</p>
                    <p className="mt-1 text-xs text-slate-400">JPEG, PNG, WebP or GIF · up to 8 MB</p>
                  </>
                )}
                <input ref={inputRef} type="file" accept="image/*" className="hidden"
                  onChange={(e) => acceptFile(e.target.files?.[0])} />
              </div>
              <button onClick={() => void capture()}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-100">
                <CameraIcon className="h-4 w-4" /> Take a photo with the camera
              </button>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Observed symptoms <span className="text-slate-400">(optional)</span>
              </label>
              <textarea className={`${inputClass} min-h-20`} value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                placeholder="e.g. Yellow leaves and brown spots" />
            </div>

            <Button className="w-full" onClick={() => analyze.mutate()} disabled={!canAnalyze}>
              <ScanSearch className="h-4 w-4" /> {analyze.isPending ? 'Analyzing…' : 'Analyze Plant'}
            </Button>

            {analyze.isPending && (
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p className="mb-2 text-xs font-medium text-slate-500">Processing pipeline</p>
                <ol className="space-y-1.5">
                  {STEPS.map((s, i) => (
                    <li key={s} className={`flex items-center gap-2 text-xs ${
                      i <= step ? 'text-brand-700 font-medium' : 'text-slate-400'}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${i <= step ? 'bg-brand-500' : 'bg-slate-300'}`} />
                      {s}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </Card>

        <Card title="Step 2 · Result">
          {analyze.isError && <ErrorState message={(analyze.error as Error).message} />}
          {!result && !analyze.isPending && (
            <div className="flex flex-col items-center justify-center py-14 text-center">
              <div className="rounded-2xl bg-brand-50 p-4 text-3xl">🪴</div>
              <p className="mt-3 text-sm font-medium text-slate-600">No analysis yet</p>
              <p className="mt-1 max-w-xs text-xs text-slate-400">
                Pick a plant, upload a leaf image, add symptoms and press "Analyze Plant".
              </p>
            </div>
          )}
          {analyze.isPending && <Spinner label="Running the analysis pipeline…" />}
          {result && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="green">{result.predicted_condition}</Badge>
                <Badge tone="blue">{Math.round(result.confidence * 100)}% (demo)</Badge>
                <Badge tone="amber">Demo Vision Model</Badge>
              </div>
              <Button variant="secondary" className="w-full"
                onClick={() => navigate(`/analysis/${result.id}`)}>
                Open full saved report
              </Button>
            </div>
          )}
        </Card>
      </div>

      {result && <AnalysisReport analysis={result} />}
    </div>
  );
}
