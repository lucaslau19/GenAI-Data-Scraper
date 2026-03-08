'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Sparkles, Globe, Upload } from 'lucide-react';

const EXAMPLE_SITES = [
  { label: 'Microsoft 365 Blog', url: 'https://www.microsoft.com/en-us/microsoft-365/blog/' },
  { label: 'Salesforce News',    url: 'https://www.salesforce.com/news/' },
  { label: 'OpenAI Blog',        url: 'https://openai.com/blog' },
  { label: 'Google AI Blog',     url: 'https://blog.google/technology/ai/' },
];

export default function HomePage() {
  const router = useRouter();
  const [urlInput, setUrlInput] = useState('');
  const [error, setError] = useState('');

  function parseUrls(raw: string): string[] {
    return raw
      .split(/[\n,]+/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);
  }

  function validateUrls(urls: string[]): string | null {
    for (const url of urls) {
      try {
        const parsed = new URL(url);
        if (!['http:', 'https:'].includes(parsed.protocol)) {
          return `Invalid URL: "${url}" — only http/https is supported.`;
        }
      } catch {
        return `Invalid URL: "${url}"`;
      }
    }
    return null;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    const urls = parseUrls(urlInput);

    if (urls.length === 0) {
      setError('Please enter at least one URL.');
      return;
    }

    const validationError = validateUrls(urls);
    if (validationError) {
      setError(validationError);
      return;
    }

    const params = new URLSearchParams({ urls: JSON.stringify(urls) });
    router.push(`/analyze?${params.toString()}`);
  }

  function addExample(url: string) {
    setUrlInput((prev) => {
      const existing = parseUrls(prev);
      if (existing.includes(url)) return prev;
      return prev ? `${prev}\n${url}` : url;
    });
    setError('');
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-4">
      {/* Header bar */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-2xl space-y-8">
        {/* Hero */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-sm font-medium px-4 py-1.5 rounded-full">
            <Sparkles className="w-4 h-4" />
            AI-Powered Competitive Intelligence
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 dark:text-white">
            GenAI Competitive Insights
          </h1>
          <p className="text-lg text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Paste competitor URLs below. The system scrapes the pages, builds a semantic
            knowledge base, and lets you ask natural-language questions.
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700 p-8 space-y-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">
                <Globe className="inline w-4 h-4 mr-1 -mt-0.5" />
                Article or Homepage URLs
              </label>
              <textarea
                value={urlInput}
                onChange={(e) => { setUrlInput(e.target.value); setError(''); }}
                placeholder={EXAMPLE_SITES.map((s) => s.url).join('\n')}
                rows={5}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-900 dark:text-white px-4 py-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none transition-colors placeholder:text-slate-300 dark:placeholder:text-slate-600"
              />
              <p className="mt-1.5 text-xs text-slate-400">
                One URL per line or comma-separated. Homepages are crawled for article links automatically.
              </p>
            </div>

            {/* Example chips */}
            <div>
              <p className="text-xs font-medium text-slate-400 dark:text-slate-500 mb-2">
                Quick-add examples:
              </p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_SITES.map((site) => (
                  <button
                    key={site.url}
                    type="button"
                    onClick={() => addExample(site.url)}
                    className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-1.5 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 dark:hover:bg-slate-600 dark:hover:text-blue-400 transition-colors"
                  >
                    {site.label}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg px-4 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={!urlInput.trim()}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors text-sm"
            >
              Analyze Articles →
            </button>
          </form>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-3 text-xs text-slate-400 dark:text-slate-500">
          {['Semantic search', 'LLM synthesis', 'Citation tracking', 'No API key required'].map((f) => (
            <span key={f} className="flex items-center gap-1">
              <span className="text-green-500">✓</span> {f}
            </span>
          ))}
        </div>
      </div>
    </main>
  );
}
