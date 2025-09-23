'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation'; // ⭐️ 追加：遷移用
// import './css/form-page.css'; // ⭐️ 追加：外部CSSを読み込み（パスは実環境に合わせて）

export default function FormPage() {
  const router = useRouter(); // ⭐️ 追加

  // 入力値（画面の状態）
  const [format, setFormat] = useState<'縦' | '横'>('縦');
  const [seconds, setSeconds] = useState<16 | 24 | 32>(24);
  const [progression, setProgression] = useState<'ナレーション型' | '登場人物型'>('ナレーション型');
  const [highlight, setHighlight] = useState('');

  // サーバーからの結果と送信状況
  const [result, setResult] = useState('');
  const [submitting, setSubmitting] = useState(false);
  // ⭐️ 追加：カウントダウン用
  const [countdown, setCountdown] = useState<number | null>(null);

  // 入力チェック（50字以内）
  const remaining = 50 - highlight.length;
  const isHighlightTooLong = remaining < 0;

  // ⭐️ 変更：/api/form にPOST → 返答を持って /chat に遷移
  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isHighlightTooLong) return;

    setSubmitting(true);
    setCountdown(20); // ⭐️ 追加：20秒カウントダウン開始
    setResult('');
    try {
      const res = await fetch('/api/form', {                 // ← /api/chat → /api/form
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ format, seconds, progression, highlight }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // 返答テキストを取り出す（reply を優先。無ければ丸ごとJSONに）
      const init: string =
        typeof data === 'string'
          ? data
          : (data.reply as string | undefined) ?? JSON.stringify(data);

      // URL に載せない
      sessionStorage.setItem('chatInit', init);

      const projectFolder: string =
        (typeof data === 'object' && data?.project_folder) || 'defaultProject';

      sessionStorage.setItem('projectFolder', projectFolder);

      router.push('/chat');

      // 遷移：/chat?init=...（⭐️ 追加）
      router.push(`/chat?init=${encodeURIComponent(init)}`);

      // 一応ページ上にも表示（任意）
      setResult(init || 'OK');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setResult('送信エラー: ' + msg);
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (countdown === null) return;
    if (countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => (prev !== null ? prev - 1 : null));
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);



  return (
    <main className="container formPage">
      <h1 className="pageTitle">映像条件の入力</h1>
      <section className="card">
        <form onSubmit={onSubmit} className="formGrid">          {/* 映像形態 */}
          <div>
            <label className="label">映像形態</label>
            <div className="row">
              <label className="radio">                <input
                type="radio"
                name="format"
                value="縦"
                checked={format === '縦'}
                onChange={() => setFormat('縦')}
              />
                <span className="chip">{format === '縦' ? '●' : '○'} 縦（スマホ向け）</span>

              </label>
              <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <input
                  type="radio"
                  name="format"
                  value="横"
                  checked={format === '横'}
                  onChange={() => setFormat('横')}
                />
                横
              </label>
            </div>
          </div>

          {/* 秒数 */}
          <div>
            <label className="label">秒数</label>
            <select
              className="input"
              value={seconds}
              onChange={(e) => setSeconds(Number(e.target.value) as 16 | 24 | 32)}
            >
              <option value={16}>16秒</option>
              <option value={24}>24秒</option>
              <option value={32}>32秒</option>
            </select>
          </div>

          {/* 映像の進行 */}
          <div>
            <label className="label">登場人物の有無</label>
            <select
              className="input"
              value={progression}
              onChange={(e) => setProgression(e.target.value as 'ナレーション型' | '登場人物型')}
            >
              <option value="ナレーション型">メイン人物なし</option>
              <option value="登場人物型">メイン人物あり</option>
            </select>
          </div>

          {/* 推したいポイント（50字以内） */}
          <div>
            <label className="label">
              推したいポイント、特徴 <span className="muted">(50字以内)</span>            </label>
            <textarea
              className="textarea"
              value={highlight}
              onChange={(e) => setHighlight(e.target.value)}
              maxLength={50}
              placeholder="例）名産の柑橘の香りとやさしい口当たりを推したい"
              rows={3}
            />
            <div className={`counter ${isHighlightTooLong ? 'danger' : 'muted'}`}>
              残り {Math.max(0, remaining)} 文字
            </div>
          </div>

          {/* ボタン行 */}
          <div className="row end">
            {/* <a className="btn btn--ghost" href="/storyboard">絵コンテを見る</a> */}
            <button className="btn" type="submit" disabled={submitting || isHighlightTooLong}>
              {submitting ? '映像条件を送信中…' : '映像条件を送信する(対話を開始する)'}
            </button>
          </div>
        </form>
      </section>
      {submitting && (
        <section className="card slim" style={{ marginTop: '16px' }}>
          <div className="label">予想待ち時間</div>
          <p>
            {countdown !== null && countdown > 0
              ? `${countdown} 秒程度お待ちください…`
              : '間も無く遷移します'}
          </p>
        </section>

      )}
      {/* <section className="card slim">
        <div className="label">サーバーからの結果</div>
        <pre className="result">{result || '（まだ結果はありません）'}</pre>      </section> */}
    </main>
  );
}
