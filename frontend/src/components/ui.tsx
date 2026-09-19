import { type ReactNode } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Loader2, X } from 'lucide-react';

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-slate-500">
      <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}

export function EmptyState({ title, subtitle, action }: {
  title: string; subtitle?: string; action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 py-16 text-center">
      <p className="text-base font-semibold text-slate-700">{title}</p>
      {subtitle && <p className="mt-1 max-w-md text-sm text-slate-500">{subtitle}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {message}
    </div>
  );
}

const TONES: Record<string, string> = {
  green: 'bg-brand-100 text-brand-800 border-brand-200',
  amber: 'bg-amber-100 text-amber-800 border-amber-200',
  red: 'bg-red-100 text-red-700 border-red-200',
  blue: 'bg-sky-100 text-sky-800 border-sky-200',
  slate: 'bg-slate-100 text-slate-600 border-slate-200',
};

export function Badge({ tone = 'slate', children }: {
  tone?: keyof typeof TONES | string; children: ReactNode;
}) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONES[tone] ?? TONES.slate}`}>
      {children}
    </span>
  );
}

export function healthTone(status: string): string {
  if (status === 'Healthy') return 'green';
  if (status === 'Needs Attention') return 'red';
  if (status === 'Monitor') return 'amber';
  return 'slate';
}

export function riskTone(risk: string | null | undefined): string {
  if (risk === 'High' || risk === 'Critical') return 'red';
  if (risk === 'Moderate') return 'amber';
  if (risk === 'Low') return 'green';
  return 'slate';
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export function pct(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function StatCard({ label, value, hint, icon, accent }: {
  label: string; value: ReactNode; hint?: string;
  icon?: ReactNode; accent?: boolean;
}) {
  return (
    <div className={`rounded-2xl border bg-white p-5 shadow-sm ${accent ? 'border-brand-200' : 'border-slate-200'}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        {icon && (
          <div className={`rounded-xl p-2.5 ${accent ? 'bg-brand-50 text-brand-600' : 'bg-slate-100 text-slate-500'}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export function Card({ title, subtitle, actions, children, className }: {
  title?: string; subtitle?: string; actions?: ReactNode;
  children: ReactNode; className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-slate-200 bg-white shadow-sm ${className ?? ''}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            {title && <h2 className="text-sm font-semibold text-slate-800">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export function Button({ children, onClick, type = 'button', variant = 'primary',
                         disabled, className }: {
  children: ReactNode; onClick?: () => void; type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'; disabled?: boolean; className?: string;
}) {
  const styles = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm',
    secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
    danger: 'border border-red-200 bg-white text-red-600 hover:bg-red-50',
    ghost: 'text-slate-600 hover:bg-slate-100',
  }[variant];
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className ?? ''}`}>
      {children}
    </button>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  'w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100';

export function Modal({ open, onOpenChange, title, children }: {
  open: boolean; onOpenChange: (open: boolean) => void;
  title: string; children: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-slate-900/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 max-h-[90vh] w-[min(560px,92vw)] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-xl focus:outline-none">
          <div className="mb-4 flex items-center justify-between">
            <Dialog.Title className="text-lg font-semibold text-slate-900">{title}</Dialog.Title>
            <Dialog.Close asChild>
              <button className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600" aria-label="Close">
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

