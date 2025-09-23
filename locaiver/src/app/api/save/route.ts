// src/app/api/save/route.ts
import type { NextRequest } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  const body = await req.text();

  // BOT_URL があれば優先（本番のRun用）。無ければローカルFlask(5050)。
  const target = (process.env.BOT_URL?.replace(/\/$/, '')) ?? 'http://127.0.0.1:5050';
  const url = `${target}/save`;

  const upstream = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
    cache: 'no-store',
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'content-type': upstream.headers.get('content-type') ?? 'application/json',
      'cache-control': 'no-store',
    },
  });
}
