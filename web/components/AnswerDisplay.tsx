import { Bot, Sparkles } from 'lucide-react';

interface Props {
  answer: string;
  usedLlm: boolean;
}

export function AnswerDisplay({ answer, usedLlm }: Props) {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/20 border border-blue-200 dark:border-blue-800/50 rounded-2xl p-6 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white shrink-0">
          <Bot className="w-4 h-4" />
        </div>
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">AI Answer</h3>
        {usedLlm && (
          <span className="ml-auto inline-flex items-center gap-1 text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300 px-2.5 py-1 rounded-full border border-blue-200 dark:border-blue-700">
            <Sparkles className="w-3 h-3" />
            GPT-4o-mini
          </span>
        )}
        {!usedLlm && (
          <span className="ml-auto text-xs text-slate-400 dark:text-slate-500 italic">
            Retrieval-only (no LLM key)
          </span>
        )}
      </div>

      {/* Answer text */}
      <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
        {answer}
      </p>
    </div>
  );
}
