import { runtime, proxyJson } from '@/lib/upstream';
export { runtime };

export async function POST(req: Request) {
  return proxyJson('/video', req);
}
