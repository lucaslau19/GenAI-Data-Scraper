import { NextRequest, NextResponse } from 'next/server';

const PYTHON_API = process.env.PYTHON_API_URL ?? 'http://localhost:8000';

export async function GET(_req: NextRequest): Promise<NextResponse> {
  try {
    const upstream = await fetch(`${PYTHON_API}/api/embed/status`, {
      signal: AbortSignal.timeout(5_000),
      cache: 'no-store',
    });
    const data: unknown = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    const raw = err instanceof Error ? err.message : 'Status check failed';
    const message = raw.toLowerCase().includes('fetch failed') || raw.toLowerCase().includes('econnrefused')
      ? 'Cannot reach the Python backend. Make sure it is running: uvicorn src.api.main:app --port 8000'
      : raw;
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
