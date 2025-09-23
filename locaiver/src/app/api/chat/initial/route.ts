import type { NextRequest } from 'next/server';

export const runtime = 'nodejs';

export async function GET() {
  const target = process.env.BOT_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:5050';
  const upstream = await fetch(`${target}/chat-initial`, { headers: { accept: 'application/json' }, cache: 'no-store' });
  return new Response(upstream.body, { status: upstream.status, headers: { 'content-type': 'application/json' } });
}

