import { useState } from 'react';
import { toast } from 'sonner';
import { Server, CheckCircle2, XCircle } from 'lucide-react';
import { Badge, Button, Card, inputClass } from '../components/ui';
import { api, getServerUrl, hasServerUrl, isNative, setServerUrl } from '../lib/api';

/**
 * Settings screen. On Android/iOS the native app does not bundle the Python
 * backend, so the user connects it to a PlantMind server on their LAN
 * (e.g. http://192.168.1.5:8000). In the browser this screen just reports
 * that the app talks to the same-origin backend.
 */
export function SettingsPage() {
  const [url, setUrl] = useState(getServerUrl());
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<'ok' | 'fail' | null>(null);

  const native = isNative();

  async function test() {
    if (!url.trim()) { toast.error('Enter the backend address first.'); return; }
    setTesting(true); setResult(null);
    setServerUrl(url);
    try {
      const health = await api.health();
      setResult('ok');
      toast.success(`Connected: PlantMind API ${'version' in health ? (health as { version?: string }).version : ''}`.trim());
    } catch {
      setResult('fail');
      toast.error('Could not reach the backend at that address.');
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Settings</h1>
        <p className="mt-0.5 text-sm text-slate-500">App connection and information.</p>
      </div>

      <Card title="Backend server" subtitle={native
        ? 'The PlantMind mobile app talks to your PlantMind backend over the local network.'
        : 'Running in a browser — the same-origin backend is used automatically.'}>
        {native ? (
          <div className="space-y-3">
            <input className={inputClass} value={url}
              onChange={(e) => { setUrl(e.target.value); setResult(null); }}
              placeholder="http://192.168.1.5:8000" inputMode="url"
              autoCapitalize="off" autoCorrect="off" spellCheck={false} />
            <div className="flex items-center gap-2">
              <Button onClick={() => void test()} disabled={testing}>
                {testing ? 'Testing…' : 'Test & Save connection'}
              </Button>
              {result === 'ok' && <Badge tone="green"><CheckCircle2 className="h-3.5 w-3.5" /> Reachable</Badge>}
              {result === 'fail' && <Badge tone="red"><XCircle className="h-3.5 w-3.5" /> Not reachable</Badge>}
            </div>
            <p className="text-xs leading-relaxed text-slate-400">
              Run the backend on a PC on the same Wi-Fi network:
              <br />
              <code className="rounded bg-slate-100 px-1 py-0.5">uvicorn backend.app.main:app --host 0.0.0.0 --port 8000</code>
              <br />
              Then enter the PC&apos;s IP address here, e.g. <code className="rounded bg-slate-100 px-1 py-0.5">http://192.168.1.5:8000</code>.
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Server className="h-4 w-4 text-brand-600" /> Connected to the local backend (http://127.0.0.1:8000 proxy).
          </div>
        )}
      </Card>

      <Card title="About">
        <ul className="space-y-1.5 text-sm text-slate-600">
          <li>PlantMind 1.0 — Explainable AI plant-care system</li>
          <li>Knowledge Graph · GraphRAG · Demo Vision Model</li>
          <li>Predictions are demo values, not guaranteed diagnoses.</li>
        </ul>
      </Card>
    </div>
  );
}