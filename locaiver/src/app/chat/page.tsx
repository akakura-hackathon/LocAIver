'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// 型
type Msg = { role: 'user' | 'bot'; text: string; typing?: boolean };

export default function ChatPage() {
  const router = useRouter();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false); // /chat 送信ローディング
  const [finLoading, setFinLoading] = useState(false); // /chat-fin 専用ローディング
  // ⭐️ 追加：/chat-fin 用カウントダウン
  const [finCountdown, setFinCountdown] = useState<number | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  // スクロール追従
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [msgs]);

  // 初期メッセージ
  useEffect(() => {
    const urlInit = typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('init')
      : null;
    const ssInit = typeof window !== 'undefined'
      ? sessionStorage.getItem('chatInit')
      : null;

    const init = urlInit ?? ssInit;
    if (init && msgs.length === 0) {
      setMsgs([{ role: 'bot', text: init }]);
      sessionStorage.removeItem('chatInit');
      // router.replace('/chat'); // ← クエリを消したいときだけ有効化
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ⭐️ 追加：/chat-fin 中だけ 1 秒ごとに減算
  useEffect(() => {
    if (!finLoading) return;
    if (finCountdown === null || finCountdown <= 0) return;

    const timer = setInterval(() => {
      setFinCountdown((prev) => (prev !== null ? Math.max(0, prev - 1) : null));
    }, 1000);

    return () => clearInterval(timer);
  }, [finLoading, finCountdown]);


  // 共通: 送信後に入力欄を“UI上”で毎回リセット & フォーカス
  const resetInputUI = () => {
    setInput('');
    // 値は state でクリア、キャレット/フォーカスは DOM で調整
    requestAnimationFrame(() => inputRef.current?.focus());
  };

  // pending バブルの差し替えヘルパ
  const replaceTypingWith = (text: string) => {
    setMsgs((m) => {
      const idx = [...m].reverse().findIndex((x) => x.role === 'bot' && x.typing);
      if (idx === -1) return [...m, { role: 'bot', text }];
      const ri = m.length - 1 - idx; // 末尾からの相対 → 実インデックス
      const next = [...m];
      next[ri] = { role: 'bot', text };
      return next;
    });
  };

  // 送信処理
  async function send() {
    if (!input.trim() || loading || finLoading) return;

    const text = input.trim();
    resetInputUI();

    const prev = msgs;
    const nextMsgs = prev.concat({ role: 'user', text });
    setMsgs(nextMsgs);

    const projectFolder = typeof window !== 'undefined'
      ? sessionStorage.getItem('projectFolder')
      : null;

    try {
      if (text === '会話終了') {
        setFinLoading(true);
        setFinCountdown(400); // ⭐️ 追加：400秒カウント開始
        // 🧠 考え中バブル（/chat-fin 用）
        setMsgs((m) => [
          ...m,
          { role: 'bot', text: 'カラー絵コンテを作成中… 少しお待ちください', typing: true },
        ]);

        const finRes = await fetch('/api/chat-fin', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ project_folder: projectFolder, messages: nextMsgs, input: text }),
        });
        if (!finRes.ok) throw new Error(`HTTP ${finRes.status}`);

        const finData = await finRes.json();
        localStorage.setItem('storyboardData', JSON.stringify(finData));
        // 置換してから遷移（任意）
        replaceTypingWith('カラー絵コンテの準備ができました。遷移します…');
        router.push('/storyboard');
        return; // NOTE: /storyboard へ遷移
      }

      // 通常メッセージ: 🧠 考え中バブルを先に出す
      setLoading(true);
      setMsgs((m) => [
        ...m,
        { role: 'bot', text: '…返信を考え中', typing: true },
      ]);

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ project_folder: projectFolder, messages: nextMsgs, input: text }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: { reply?: string; meta?: unknown } = await res.json();
      replaceTypingWith(data.reply ?? 'OK');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      replaceTypingWith('エラーが発生しました: ' + msg);
    } finally {
      setLoading(false);
      setFinLoading(false);
      setFinCountdown(null); // ⭐️ 追加：後片付け
    }
  }

  // キー操作: Enter単押しでは送信しない。Ctrl(Command)+Enterで送信。
  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    const isEnter = e.key === 'Enter';
    const withCtrlOrMeta = e.ctrlKey || e.metaKey; // Windows/Linux: Ctrl, macOS: Command

    if (isEnter && withCtrlOrMeta) {
      e.preventDefault();
      send();
    }
    // それ以外（Enter単押し/Shift+Enter）はテキストエリアの改行として扱う
  }

  // 保存
  async function saveTranscript() {
    try {
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ messages: msgs }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setMsgs((m) => [...m, { role: 'bot', text: '会話ログを保存しました（/save）' }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setMsgs((m) => [...m, { role: 'bot', text: '保存に失敗しました: ' + msg }]);
    }
  }

  // ダウンロード
  function downloadTranscript() {
    const blob = new Blob([JSON.stringify({ messages: msgs }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const anyLoading = loading || finLoading;

  return (
    <section className="card" style={{ position: 'relative' }}>
      <h1 style={{ marginTop: 0, color: 'var(--primary-ink)', display: 'flex', alignItems: 'center', gap: 8 }}>
        対話画面
        {anyLoading && (
          <span className="spinner" aria-live="polite" aria-label={finLoading ? 'カラー絵コンテを作成中' : '送信中'} />
        )}
      </h1>

      {/* 履歴エリア */}
      <div
        ref={listRef}
        className="card"
        style={{ maxHeight: 520, overflow: 'auto', marginBottom: 12 }}
        aria-live="polite"
      >
        {msgs.map((m, i) => (
          <div
            key={i}
            style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}
          >
            <div
              style={{
                background: m.role === 'user'
                  ? 'linear-gradient(160deg, var(--accent-2) 0%, #ffd88a 100%)'
                  : '#ffffff',
                color: m.role === 'user' ? '#6a4b00' : 'var(--text)',
                border: '1px solid var(--border)',
                borderRadius: 14,
                padding: '10px 12px',
                margin: '6px 0',
                boxShadow: 'var(--shadow-sm)',
                maxWidth: '75%',
                wordBreak: 'break-word',
              }}
            >
              {/* マークダウン表示 */}
              <div style={{ whiteSpace: 'normal' }}>
                {m.typing ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span className="spinner" />
                    <span>{m.text}</span>
                  </span>
                ) : (
                  <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.text}
                  </ReactMarkdown></div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 入力行 */}
      <div className="row" style={{ alignItems: 'center', gap: 8 }}>
        <textarea
          ref={inputRef}
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder='メッセージを入力（Ctrl/⌘+Enterで送信。「会話終了」で締め）'
          aria-label="メッセージ入力"
          rows={3}
          style={{ resize: 'vertical' }}
        />
        <button className="btn" onClick={send} disabled={!input.trim() || anyLoading} aria-busy={anyLoading}>
          {finLoading ? 'カラー絵コンテを作成中…' : loading ? '送信中…' : '送信'}
        </button>
      </div>

      {/* /chat-fin 中は画面右下にスナック表示（任意） */}
      {finLoading && (
        <div
          role="status"
          aria-live="assertive"
          style={{
            position: 'absolute',
            right: 12,
            bottom: 12,
            background: 'rgba(255,255,255,0.95)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            padding: '8px 12px',
            boxShadow: 'var(--shadow-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span className="spinner" />
          <span>
            カラー絵コンテを作成中…
            {' '}
            {finCountdown !== null && finCountdown > 0
              ? `${finCountdown} 秒程度お待ちください…`
              : '間も無く遷移します'}
          </span>
        </div>
      )}

      <style jsx>{`
        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid var(--border);
          border-top-color: var(--primary-ink);
          border-radius: 50%;
          display: inline-block;
          animation: spin 0.9s linear infinite;
        }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        /* Markdown 基本スタイル */
        :global(.md) { white-space: pre-wrap; }
        :global(.md p) { margin: 0.2em 0; }
        :global(.md h1), :global(.md h2), :global(.md h3) { margin: 0.4em 0 0.2em; font-weight: 700; }
        :global(.md code) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #f6f8fa; padding: 0.1em 0.3em; border-radius: 4px; }
        :global(.md pre) { background: #f6f8fa; padding: 8px; border-radius: 8px; overflow: auto; }
        :global(.md a) { color: var(--primary-ink); text-decoration: underline; }
        :global(.md ul), :global(.md ol) { padding-left: 1.2em; margin: 0.2em 0; }
        :global(.md blockquote) { border-left: 3px solid #ddd; padding-left: 8px; color: #555; margin: 0.3em 0; }
      `}</style>
    </section>
  );
}
