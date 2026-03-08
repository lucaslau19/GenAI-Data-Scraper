export interface Article {
  url: string;
  title: string;
  scraped_at: string;
  content: string;
  word_count: number;
  source_name?: string;
}

export interface Chunk {
  source: string;
  source_name?: string;
  title: string;
  scraped_at: string;
  chunk_id: number;
  total_chunks: number;
  text: string;
  char_count: number;
}

export interface SearchResult {
  chunk: Chunk;
  distance: number;
  relevance_score: number;
  rank: number;
}

export interface QueryResponse {
  answer: string;
  results: SearchResult[];
  used_llm: boolean;
  sources: string[];
}

export interface ScrapeResponse {
  scraped: number;
  failed: number;
  articles: Article[];
}

export interface EmbedStatusResponse {
  status: 'idle' | 'running' | 'done' | 'error';
  message: string;
  progress: number;
  error: string | null;
}

export type ProcessingStep = 'idle' | 'scraping' | 'embedding' | 'done' | 'error';

export interface ProcessingState {
  step: ProcessingStep;
  message: string;
  progress: number;
  scrapedCount: number;
}
