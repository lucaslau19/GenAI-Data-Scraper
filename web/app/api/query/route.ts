import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API = process.env.PYTHON_API_URL ?? 'http://localhost:8000';

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const body: unknown = await req.json();
    const upstream = await fetch(`${PYTHON_API}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
    });
    const data: unknown = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    const raw = err instanceof Error ? err.message : 'Query request failed';
    const message = raw.toLowerCase().includes('fetch failed') || raw.toLowerCase().includes('econnrefused')
      ? 'Cannot reach the Python backend. Make sure it is running: uvicorn src.api.main:app --port 8000'
      : raw;
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
