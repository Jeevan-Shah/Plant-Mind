import { useEffect, useRef, useState } from 'react';
import { Bot, Loader2, Send } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import type { ChatTurn } from '../types';
import { Button, Card, inputClass } from './ui';

const QUICK_QUESTIONS = [
  'How often should I water it?',
  'Is this serious?',
  'What treatment should I use?',
  'Why did it predict this?',
  'Will it spread to other plants?',
];

interface LocalTurn extends ChatTurn {
  pending?: boolean;
}

function Avatar() {
  return (
    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
      <Bot className="h-4 w-4" />
    </span>
  );
}

export function ChatAssistant({ analysisId, plantName }: {
  analysisId: number; plantName: string | null;
}) {
  const [turns, setTurns] = useState<LocalTurn[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns]);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || busy) return;
    setInput('');
    const history: ChatTurn[] = [
      ...turns.filter((t) => !t.pending && t.content),
      { role: 'user', content: question },
    ];
    setTurns([...history, { role: 'assistant', content: '', pending: true }]);
    setBusy(true);
    try {
      const res = await api.chat(
        analysisId,
        history.map((t) => ({ role: t.role, content: t.content })),
      );
      setTurns([...history, { role: 'assistant', content: res.answer, sources: res.sources, mode: res.mode }]);
    } catch (e) {
      setTurns(history);
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      title="Ask PlantMind"
      subtitle="Still have doubts? Ask a follow-up — every answer is grounded in the knowledge graph for this result"
      actions={
        <span className="rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-medium text-brand-700">
          Chat
        </span>
      }
    >
      <div ref={scrollRef} className="max-h-80 space-y-3 overflow-y-auto pr-1">
        {turns.length === 0 && (
          <div className="flex items-start gap-3">
            <Avatar />
            <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-slate-100 px-3.5 py-2.5 text-sm leading-relaxed text-slate-700">
              Hi! I can explain this result for {plantName ?? 'your plant'} — watering, light,
              treatment, spread risk, prevention, or why this diagnosis was chosen.
              What would you like to know?
            </div>
          </div>
        )}
        {turns.map((t, i) =>
          t.role === 'user' ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-brand-600 px-3.5 py-2 text-sm leading-relaxed text-white">
                {t.content}
              </div>
            </div>
          ) : t.pending ? (
            <div key={i} className="flex items-start gap-3">
              <Avatar />
              <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-slate-100 px-3.5 py-2.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400" />
                <span className="text-xs text-slate-400">Thinking…</span>
              </div>
            </div>
          ) : (
            <div key={i} className="flex items-start gap-3">
              <Avatar />
              <div className="min-w-0 max-w-[85%]">
                <div className="whitespace-pre-wrap rounded-2xl rounded-tl-sm bg-slate-100 px-3.5 py-2.5 text-sm leading-relaxed text-slate-700">
                  {t.content}
                </div>
                {t.sources && t.sources.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {t.sources.map((s, j) => (
                      <span
                        key={j}
                        title={`${s.label}: ${s.detail}`}
                        className="max-w-56 truncate rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[10px] text-slate-500"
                      >
                        {s.label}: {s.detail}
                      </span>
                    ))}
                  </div>
                )}
                {t.mode && (
                  <p className="mt-1 font-mono text-[10px] text-slate-400">{t.mode}</p>
                )}
              </div>
            </div>
          ),
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => send(q)}
            disabled={busy}
            className="rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-100 disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(input); }}
        className="mt-3 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
          placeholder="Type your doubt…"
          className={inputClass}
        />
        <Button type="submit" disabled={busy || !input.trim()}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Send
        </Button>
      </form>
    </Card>
  );
}