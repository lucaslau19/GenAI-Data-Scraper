'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';

const EXAMPLE_QUERIES = [
  "What are the main competitive insights?",
  "What products did Microsoft announce?",
  "What is Salesforce's latest strategy?",
  "Compare AI features across companies",
  "What partnerships were announced?",
];

interface Props {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function QueryInterface({ onSearch, isLoading }: Props) {
  const [query, setQuery] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q || isLoading) return;
    onSearch(q);
  }

  function pickExample(q: string) {
    setQuery(q);
    if (!isLoading) onSearch(q);
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the analyzed articles…"
            disabled={isLoading}
            className="w-full pl-9 pr-4 py-3 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="px-5 py-3 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors text-sm shrink-0"
        >
          {isLoading ? 'Searching…' : 'Search'}
        </button>
      </form>

      <div>
        <p className="text-xs text-slate-400 dark:text-slate-500 mb-2 font-medium">Try an example:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => pickExample(q)}
              disabled={isLoading}
              className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 rounded-full px-3 py-1.5 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 dark:hover:bg-slate-600 dark:hover:text-blue-400 transition-colors disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
