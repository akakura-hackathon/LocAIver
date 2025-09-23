'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * 動画表示ページ（シンプル版）
 * - 画面比率は "横長(16:9)" に固定
 * - 表示は常に "余白あり(contain)" に固定（レターボックス）
 * - 余計なボタン/トグル類は非表示
 * - sessionStorage の `videoUrl` または `?src=` から URL を取得
 * - 読み込み/バッファ中はスピナー表示
 */

export default function VideoPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [src, setSrc] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [buffering, setBuffering] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // URLを sessionStorage またはクエリから取得（src クエリを優先）
  useEffect(() => {
    const sp = new URLSearchParams(window.location.search);
    const qSrc = sp.get('src') || '';
    const initialSrc = qSrc || sessionStorage.getItem('videoUrl') || '';
    setSrc(initialSrc);
  }, []);

  const handleLoadedMetadata = () => {
    setLoading(false);
  };

  const handleWaiting = () => setBuffering(true);
  const handlePlaying = () => setBuffering(false);

  const canPlay = !!src && !err;

  return (
    <main className="container" style={{ paddingBottom: 24 }}>
      <h1 className="pageTitle" style={{ color: 'var(--primary-ink)', marginBottom: 12 }}>完成映像</h1>

      <section className="card" style={{ position: 'relative' }}>
        {!src && (
          <div className="card" style={{ marginBottom: 12 }}>
            <div className="label">動画URLが指定されていません</div>
            <p style={{ margin: 0 }}>Storyboard から映像作成を行ってください。</p>
          </div>
        )}

        {/* 16:9 固定フレーム（常に余白ありで全体表示） */}
        <div className="video-frame" style={{ aspectRatio: '16 / 9' }}>
          {canPlay && (
            <video
              ref={videoRef}
              src={src}
              controls
              playsInline
              onLoadedMetadata={handleLoadedMetadata}
              onCanPlay={() => setLoading(false)}
              onWaiting={handleWaiting}
              onPlaying={handlePlaying}
              onError={() => { setErr('動画の読み込みに失敗しました'); setLoading(false); }}
              style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }}
            />
          )}

          {(loading || buffering) && (
            <div className="loading-overlay" role="status" aria-live="polite">
              <span className="spinner" />
              <span style={{ marginLeft: 8 }}>{loading ? '読み込み中…' : 'バッファ中…'}</span>
            </div>
          )}

          {err && (
            <div className="error-overlay" role="alert">
              <strong style={{ color: 'var(--danger)' }}>{err}</strong>
            </div>
          )}
        </div>
      </section>

      <style jsx>{`
        .video-frame {
          position: relative;
          width: 100%;
          max-width: 920px; /* 横長固定なので少し広めに */
          margin: 0 auto;
          background: #000;
          border-radius: var(--radius-xl);
          overflow: hidden;
          border: 1px solid var(--border);
          box-shadow: var(--shadow-md);
        }
        .loading-overlay {
          position: absolute;
          left: 12px; bottom: 12px;
          display: inline-flex; align-items: center;
          background: rgba(255,255,255,0.9);
          border: 1px solid var(--border);
          padding: 6px 10px; border-radius: 999px;
          box-shadow: var(--shadow-sm);
        }
        .error-overlay {
          position: absolute; inset: 0;
          display: grid; place-items: center;
          background: rgba(255, 255, 255, 0.92);
          text-align: center;
          padding: 12px;
        }
        .spinner {
          width: 16px; height: 16px;
          border: 2px solid var(--border);
          border-top-color: var(--primary-ink);
          border-radius: 50%;
          animation: spin 0.9s linear infinite;
        }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </main>
  );
}
