import { type ReactNode } from 'react';
import { Leaf, LayoutDashboard, History, Network, Plus, Sprout, Info, Settings } from 'lucide-react';
import { navigate, useRoute } from '../hooks/useRoute';
import { isNative } from '../lib/api';

const NAV = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/plants', label: 'Plants', icon: Sprout },
  { path: '/history', label: 'Analysis History', icon: History },
  { path: '/knowledge', label: 'Knowledge Explorer', icon: Network },
];

export function Layout({ children }: { children: ReactNode }) {
  const route = useRoute();
  const navItems = isNative()
    ? [...NAV, { path: '/settings', label: 'Settings', icon: Settings }]
    : NAV;
  const active = (path: string) =>
    path === '/' ? route.path === '/' : route.path.startsWith(path);

  return (
    <div className="flex min-h-full">
      {/* Sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="rounded-xl bg-brand-600 p-2">
            <Leaf className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-base font-semibold tracking-tight text-slate-900">PlantMind</p>
            <p className="text-[11px] text-slate-400">Explainable plant care</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {navItems.map(({ path, label, icon: Icon }) => (
            <button key={path} onClick={() => navigate(path)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                active(path) ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <Icon className="h-[18px] w-[18px]" />
              {label}
            </button>
          ))}
        </nav>
        <div className="px-3 pb-4">
          <button onClick={() => navigate('/analyze')}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-brand-700">
            <Plus className="h-4 w-4" /> Analyze Plant
          </button>
          <p className="mt-3 px-1 text-[11px] leading-relaxed text-slate-400">
            PlantMind provides AI-assisted plant-care guidance for educational and
            decision-support purposes. Predictions are not guaranteed diagnoses.
          </p>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="flex items-center justify-between px-4 py-3 md:px-8">
            <div className="flex items-center gap-2 md:hidden">
              <div className="rounded-lg bg-brand-600 p-1.5">
                <Leaf className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold text-slate-900">PlantMind</span>
            </div>
            <nav className="flex flex-1 gap-1 overflow-x-auto md:hidden">
              {navItems.map(({ path, label, icon: Icon }) => (
                <button key={path} onClick={() => navigate(path)} aria-label={label}
                  className={`rounded-lg p-2 ${active(path) ? 'bg-brand-50 text-brand-700' : 'text-slate-500'}`}>
                  <Icon className="h-5 w-5" />
                </button>
              ))}
            </nav>
            <p className="hidden text-xs text-slate-400 md:block">
              Knowledge Graph · GraphRAG · Demo Vision Model
            </p>
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8">
          {children}
        </main>

        <footer className="border-t border-slate-200 bg-white px-4 py-3 md:px-8">
          <p className="mx-auto flex max-w-6xl items-start gap-2 text-[11px] leading-relaxed text-slate-400">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            PlantMind provides AI-assisted plant-care guidance for educational and
            decision-support purposes. Predictions are not guaranteed diagnoses.
            Verify recommendations with reliable agricultural sources or experts when necessary.
          </p>
        </footer>
      </div>
    </div>
  );
}
