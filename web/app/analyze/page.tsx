'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ProcessingStatus } from '@/components/ProcessingStatus';
import { QueryInterface } from '@/components/QueryInterface';
import { AnswerDisplay } from '@/components/AnswerDisplay';
import { ResultCard } from '@/components/ResultCard';
import { scrapeUrls, startEmbedding, getEmbedStatus, queryIndex } from '@/lib/api';
import type { ProcessingState, QueryResponse } from '@/lib/types';
import { ArrowLeft } from 'lucide-react';

function AnalyzeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [state, setState] = useState<ProcessingState>({
    step: 'idle',
    message: 'Initialising…',
    progress: 0,
    scrapedCount: 0,
  });
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollEmbedStatus = useCallback(() => {
    pollRef.current = setInterval(async () => {
      try {
        const status = await getEmbedStatus();
        setState((prev) => ({
          ...prev,
          progress: status.progress,
          message: status.message,
        }));
        if (status.status === 'done') {
          stopPolling();
          setState((prev) => ({ ...prev, step: 'done', progress: 100 }));
        } else if (status.status === 'error') {
          stopPolling();
          setState((prev) => ({ ...prev, step: 'error' }));
          setPipelineError(status.error ?? 'Embedding pipeline failed.');
        }
      } catch {
        // transient network error — keep polling
      }
    }, 1500);
  }, [stopPolling]);

  useEffect(() => {
    const raw = searchParams.get('urls');
    if (!raw) { router.push('/'); return; }

    let urls: string[];
    try {
      urls = JSON.parse(raw) as string[];
    } catch {
      router.push('/');
      return;
    }

    void runPipeline(urls);
    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runPipeline(urls: string[]) {
    try {
      // Step 1: Scrape
      setState({ step: 'scraping', message: `Scraping ${urls.length} site(s)…`, progress: 10, scrapedCount: 0 });
      const scrapeResult = await scrapeUrls(urls);

      // Step 2: Start embedding (background task)
      setState((prev) => ({
        ...prev,
        step: 'embedding',
        message: `Generating embeddings for ${scrapeResult.scraped} articles…`,
        progress: 35,
        scrapedCount: scrapeResult.scraped,
      }));
      await startEmbedding();

      // Poll for completion
      pollEmbedStatus();
    } catch (err) {
      stopPolling();
      setState((prev) => ({ ...prev, step: 'error' }));
      setPipelineError(err instanceof Error ? err.message : 'An unexpected error occurred.');
    }
  }

  async function handleQuery(query: string) {
    setQueryLoading(true);
    setQueryResponse(null);
    setQueryError(null);
    try {
      const res = await queryIndex(query);
      setQueryResponse(res);
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : 'Search failed.');
    } finally {
      setQueryLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Sticky header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-800/80 backdrop-blur border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => router.push('/')}
            className="inline-flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 font-medium hover:underline"
          >
            <ArrowLeft className="w-4 h-4" />
            New analysis
          </button>
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200 hidden sm:block">
            GenAI Competitive Insights
          </span>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Processing status card */}
        {state.step !== 'done' && (
          <section className="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-6 animate-fade-in">
            <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-5">
              Processing Articles
            </h2>
            <ProcessingStatus
              step={state.step}
              message={state.message}
              progress={state.progress}
            />
            {pipelineError && (
              <div className="mt-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
                <strong>Error:</strong> {pipelineError}
              </div>
            )}
            {state.step === 'error' && (
              <button
                onClick={() => router.push('/')}
                className="mt-4 text-sm text-blue-600 dark:text-blue-400 underline"
              >
                Try again with different URLs
              </button>
            )}
          </section>
        )}

        {/* Query interface — shown only when ready */}
        {state.step === 'done' && (
          <section className="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-6 animate-fade-in">
            <div className="flex items-center gap-2 mb-4">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 text-xs font-bold">✓</span>
              <h2 className="text-lg font-bold text-slate-800 dark:text-white">
                {state.scrapedCount} article{state.scrapedCount !== 1 ? 's' : ''} indexed — ask anything
              </h2>
            </div>
            <QueryInterface onSearch={handleQuery} isLoading={queryLoading} />
          </section>
        )}

        {/* Loading spinner */}
        {queryLoading && (
          <div className="flex justify-center py-10">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Query error */}
        {queryError && !queryLoading && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
            <strong>Search error:</strong> {queryError}
          </div>
        )}

        {/* Results */}
        {queryResponse && !queryLoading && (
          <div className="space-y-4 animate-fade-in">
            <AnswerDisplay answer={queryResponse.answer} usedLlm={queryResponse.used_llm} />

            {queryResponse.results.length > 0 && (
              <>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 pt-2">
                  Supporting Sources ({queryResponse.results.length})
                </h3>
                {queryResponse.results.map((r) => (
                  <ResultCard
                    key={`${r.chunk.source}-${r.chunk.chunk_id}`}
                    result={r}
                  />
                ))}
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <AnalyzeContent />
    </Suspense>
  );
}
