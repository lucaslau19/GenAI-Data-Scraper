import type {
  EmbedStatusResponse,
  QueryResponse,
  ScrapeResponse,
} from './types';

// In development, Next.js rewrites /api/* to the Python backend.
// Override with NEXT_PUBLIC_API_BASE if needed (e.g. for direct backend calls).
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? '/api';

async function post<T>(path: string, body: unknown, timeoutMs = 120_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const json = (await res.json()) as { detail?: string };
        if (json.detail) detail = json.detail;
      } catch {
        // ignore JSON parse error
      }
      throw new Error(detail);
    }

    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function scrapeUrls(
  urls: string[],
  maxArticlesPerSite = 5,
): Promise<ScrapeResponse> {
  return post<ScrapeResponse>('/scrape', {
    urls,
    max_articles_per_site: maxArticlesPerSite,
  });
}

export function startEmbedding(): Promise<{ status: string; message: string }> {
  return post('/embed', {});
}

export function getEmbedStatus(): Promise<EmbedStatusResponse> {
  return get<EmbedStatusResponse>('/embed/status');  // matches app/api/embed/status/route.ts
}

export function queryIndex(
  query: string,
  topK = 5,
  useLlm = true,
  sourceFilter?: string,
): Promise<QueryResponse> {
  return post<QueryResponse>('/query', {
    query,
    top_k: topK,
    use_llm: useLlm,
    source_filter: sourceFilter ?? null,
  });
}
