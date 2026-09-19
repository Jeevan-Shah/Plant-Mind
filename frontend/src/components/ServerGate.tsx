import { useState } from 'react';
import type { ReactNode } from 'react';
import { Leaf, Server } from 'lucide-react';
import { Button, inputClass } from './ui';
import { api, hasServerUrl, isNative, setServerUrl } from '../lib/api';

/**
 * First-launch gate for the native app: the APK ships without the Python
 * backend, so the user must point it at a PlantMind server on their LAN
 * before anything else can load.
 */
export function ServerGate({ children }: { children: ReactNode }) {
  const [url, setUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isNative() || hasServerUrl()) return <>{children}</>;

  async function connect() {
    if (!url.trim()) { setError('Enter the backend address first.'); return; }
    setBusy(true); setError(null);
    setServerUrl(url);
    try {
      await api.health();
      window.location.reload(); // re-render the whole app against the server
    } catch {
      setError('Could not reach the backend. Check the address, that the server is running, and that both devices are on the same Wi-Fi.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="rounded-xl bg-brand-600 p-2.5"><Leaf className="h-6 w-6 text-white" /></div>
          <div>
            <p className="text-lg font-semibold tracking-tight text-slate-900">PlantMind</p>
            <p className="text-xs text-slate-400">Connect to your plant-care server</p>
          </div>
        </div>
        <div className="mt-5 space-y-3">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-600">Backend address</span>
            <input className={inputClass} value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder="http://192.168.1.5:8000" inputMode="url"
              autoCapitalize="off" autoCorrect="off" spellCheck={false} />
          </label>
          {error && <p className="text-xs leading-relaxed text-red-600">{error}</p>}
          <Button className="w-full" onClick={() => void connect()} disabled={busy}>
            <Server className="h-4 w-4" /> {busy ? 'Connecting…' : 'Connect'}
          </Button>
          <p className="text-[11px] leading-relaxed text-slate-400">
            On a PC on the same Wi-Fi, run:
            <br />
            <code className="rounded bg-slate-100 px-1 py-0.5">uvicorn backend.app.main:app --host 0.0.0.0 --port 8000</code>
            <br />
            Then enter that PC&apos;s IP address here.
          </p>
        </div>
      </div>
    </div>
  );
}