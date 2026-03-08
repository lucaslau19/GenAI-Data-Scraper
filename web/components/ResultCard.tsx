import { ExternalLink } from 'lucide-react';
import type { SearchResult } from '@/lib/types';

function RelevanceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70
      ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800'
      : pct >= 40
      ? 'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800'
      : 'bg-slate-50 dark:bg-slate-700 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-600';

  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${color} shrink-0`}>
      {pct}% match
    </span>
  );
}

export function ResultCard({ result }: { result: SearchResult }) {
  const { chunk, relevance_score, rank } = result;

  return (
    <article className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl p-5 space-y-3 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <span className="text-xs font-mono text-slate-300 dark:text-slate-600 mr-2">
            #{rank}
          </span>
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            {chunk.title || 'Untitled'}
          </span>
          {chunk.source_name && (
            <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">
              · {chunk.source_name}
            </span>
          )}
        </div>
        <RelevanceBadge score={relevance_score} />
      </div>

      {/* Snippet */}
      <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed line-clamp-4">
        {chunk.text}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500 pt-1">
        <a
          href={chunk.source}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 truncate max-w-xs hover:text-blue-500 transition-colors group"
        >
          <ExternalLink className="w-3 h-3 shrink-0 group-hover:text-blue-500" />
          <span className="truncate">{chunk.source}</span>
        </a>
        <span className="shrink-0 ml-2 tabular-nums">
          chunk {chunk.chunk_id + 1}/{chunk.total_chunks}
        </span>
      </div>
    </article>
  );
}
