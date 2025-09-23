import { NextRequest } from 'next/server';

const BOT_URL = process.env.BOT_URL; // 本番は Run のURLを設定。未設定ならローカルモックにフォールバック。

export async function GET(_req: NextRequest) {
  try {
    const upstream = await fetch(
      BOT_URL ? `${BOT_URL.replace(/\/$/, '')}/storyboard`
              : 'http://localhost:8787/storyboard',
      { method: 'GET', headers: { 'accept': 'application/json' } }
    );

    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        'content-type': upstream.headers.get('content-type') ?? 'application/json',
        'cache-control': 'no-store',
      },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return Response.json({ error: 'failed_to_fetch_storyboard', message: msg }, { status: 502 });
  }
}
