// src/lib/upstream.ts
export const runtime = 'nodejs' as const;

export function getBase(): string | null {
  const raw = process.env.BOT_URL;
  return raw ? raw.replace(/\/$/, '') : null;
}

export function debugOn() {
  return process.env.DEBUG_PROXY === '1';
}

export async function proxyJson(subpath: string, req: Request, timeoutMs = 600_000): Promise<Response> {
  const base = getBase();
  if (!base) return Response.json({ error: 'bot_url_not_set' }, { status: 503 });

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const targetUrl = new URL(subpath, base).toString();  // ← 絶対安全に /form を合成
    console.log('proxy →', targetUrl);

    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers: { 'content-type': 'application/json' },
      body: await req.text(),           // 文字列に固定してストリーム問題回避
      cache: 'no-store',
      signal: controller.signal,
    });

    const headers = new Headers();
    headers.set('content-type', upstream.headers.get('content-type') ?? 'application/json');
    const setCookie = upstream.headers.get('set-cookie');
    if (setCookie) headers.set('set-cookie', setCookie);

    return new Response(upstream.body, { status: upstream.status, headers });
  } catch (e: unknown) {
    const aborted = e instanceof Error && e.name === 'AbortError';
    const detail = e instanceof Error ? e.message : String(e);
    console.error('proxy error', detail);
    // 開発中だけ詳細を返す
    if (debugOn()) return Response.json({ error: aborted ? 'upstream_timeout' : 'upstream_error', detail }, { status: 502 });
    return Response.json({ error: aborted ? 'upstream_timeout' : 'upstream_error' }, { status: 502 });
  } finally {
    clearTimeout(timer);
  }
}
