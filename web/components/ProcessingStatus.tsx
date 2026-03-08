import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import type { ProcessingStep } from '@/lib/types';

interface PipelineStep {
  id: ProcessingStep;
  label: string;
}

const STEPS: PipelineStep[] = [
  { id: 'scraping',  label: 'Scraping articles' },
  { id: 'embedding', label: 'Generating embeddings & building vector index' },
  { id: 'done',      label: 'Ready to query' },
];

function stepIndex(step: ProcessingStep): number {
  if (step === 'idle' || step === 'error') return -1;
  return STEPS.findIndex((s) => s.id === step);
}

interface Props {
  step: ProcessingStep;
  message: string;
  progress: number;
}

export function ProcessingStatus({ step, message, progress }: Props) {
  const currentIdx = stepIndex(step);

  return (
    <div className="space-y-5">
      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-slate-600 dark:text-slate-300 font-medium">{message}</span>
          <span className="text-slate-400 tabular-nums">{progress}%</span>
        </div>
        <div className="w-full h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Step list */}
      <ul className="space-y-3">
        {STEPS.map((s, i) => {
          const isError  = step === 'error' && i === currentIdx;
          const isDone   = step === 'done' || i < currentIdx;
          const isActive = i === currentIdx && !isError;

          return (
            <li key={s.id} className="flex items-center gap-3">
              {isError ? (
                <XCircle className="h-5 w-5 text-red-500 shrink-0" />
              ) : isDone ? (
                <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
              ) : isActive ? (
                <Loader2 className="h-5 w-5 text-blue-500 animate-spin shrink-0" />
              ) : (
                <Circle className="h-5 w-5 text-slate-200 dark:text-slate-600 shrink-0" />
              )}
              <span
                className={
                  isError
                    ? 'text-red-500 font-medium text-sm'
                    : isDone
                    ? 'text-slate-800 dark:text-slate-100 font-medium text-sm'
                    : isActive
                    ? 'text-blue-600 dark:text-blue-400 font-medium text-sm'
                    : 'text-slate-400 text-sm'
                }
              >
                {s.label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
