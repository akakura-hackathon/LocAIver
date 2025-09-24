'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

// --- 型定義 ---
type Composition = { camera_angle?: string; view?: string; focal_length?: string; lighting?: string; focus?: string; };
type Dialogue = { character: string; line: string; };
type Scene = {
  scene_id: number;
  depiction: string;
  composition?: Composition;
  dialogue?: Dialogue[];
  other_information?: string;
  url?: string;         // 画像URL
};

type Row = { id: string; name: string; content: string; line: string; photoUrl?: string; sceneId: number; };
type SceneJSON = { scenes: Scene[] };

type EditRow = { scene_id: number; input_fix: string }; // ✅ fixフラグは廃止

// ランタイム型ガード
function isSceneJSON(x: any): x is SceneJSON {
  return x && Array.isArray(x.scenes) && x.scenes.every(
    (s: any) => typeof s?.scene_id === 'number' && typeof s?.depiction === 'string'
  );
}

export default function StoryboardPage() {
  const router = useRouter();
  const [items, setItems] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [edits, setEdits] = useState<EditRow[]>([]);
  const [videoLoading, setVideoLoading] = useState(false); // ✅ 映像作成ボタンの二重押し防止 & ぐるぐる表示
  const [editLoading, setEditLoading] = useState(false);   // ✅ 編集送信ボタンの二重押し防止 & ぐるぐる表示

  const [videoCountdown, setVideoCountdown] = useState<number | null>(null);
  const [editCountdown, setEditCountdown] = useState<number | null>(null);

  function normalizeScenes(json: SceneJSON): Row[] {
    if (!json?.scenes || !Array.isArray(json.scenes)) return [];
    return json.scenes.map((s) => {
      const content = s.depiction;
      const line = (s.dialogue ?? []).map((d) => `${d.character}：${d.line}`).join('\n');
      return {
        id: `scene-${s.scene_id}`,
        name: `シーン ${s.scene_id}`,
        content,
        line: line || '-',
        photoUrl: s.url,
        sceneId: s.scene_id,
      };
    });
  }

  useEffect(() => {
  if (typeof window !== 'undefined' && sessionStorage.getItem('counter') == null) {
    sessionStorage.setItem('counter', '1'); // 初回は1として保持（送信時に+1されて2になる）
  }
}, []);

  // {scenes:[...]} を保存しつつ、画面に反映
  function applySceneJSON(parsed: unknown) {
    if (isSceneJSON(parsed)) {
      localStorage.setItem('storyboardData', JSON.stringify(parsed));
      const rows = normalizeScenes(parsed);
      setItems(rows);
      setEdits(rows.map((r) => ({ scene_id: r.sceneId, input_fix: '' })));
    } else if ((parsed as any)?.scenes && Array.isArray((parsed as any).scenes)) {
      const safe = { scenes: (parsed as any).scenes } as SceneJSON;
      localStorage.setItem('storyboardData', JSON.stringify(safe));
      const rows = normalizeScenes(safe);
      setItems(rows);
      setEdits(rows.map((r) => ({ scene_id: r.sceneId, input_fix: '' })));
    } else {
      throw new Error('サーバーの返却が { scenes: [...] } ではありません');
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const raw = typeof window !== 'undefined' ? localStorage.getItem('storyboardData') : null;
        if (raw) {
          let parsed: unknown;
          try {
            parsed = JSON.parse(raw);
          } catch (e) {
            setErr('localStorageのJSONが壊れています（JSON.parse失敗）');
            setItems([]);
            return;
          }

          if (isSceneJSON(parsed)) {
            const rows = normalizeScenes(parsed);
            setItems(rows);
            setEdits(rows.map((r) => ({ scene_id: r.sceneId, input_fix: '' })));
          } else if ((parsed as any)?.scenes && Array.isArray((parsed as any).scenes)) {
            const safe: SceneJSON = { scenes: (parsed as any).scenes };
            const rows = normalizeScenes(safe);
            setItems(rows);
            setEdits(rows.map((r) => ({ scene_id: r.sceneId, input_fix: '' })));
          } else {
            setErr('想定外の形のデータです。{ scenes: [...] } を保存してください。');
            setItems([]);
          }
          return;
        }

        setItems([]);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setErr(`データ取得に失敗しました: ${msg}`);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ⭐️ 追加：映像作成 400秒
  useEffect(() => {
    if (!videoLoading) return;
    if (videoCountdown === null || videoCountdown <= 0) return;
    const t = setInterval(() => {
      setVideoCountdown((p) => (p !== null ? Math.max(0, p - 1) : null));
    }, 1000);
    return () => clearInterval(t);
  }, [videoLoading, videoCountdown]);

  // ⭐️ 追加：編集送信 60秒
  useEffect(() => {
    if (!editLoading) return;
    if (editCountdown === null || editCountdown <= 0) return;
    const t = setInterval(() => {
      setEditCountdown((p) => (p !== null ? Math.max(0, p - 1) : null));
    }, 1000);
    return () => clearInterval(t);
  }, [editLoading, editCountdown]);


  function exportJSON() {
    const scenes: Scene[] = items.map((r, idx) => ({
      scene_id: idx + 1,
      depiction: r.content,
      dialogue: r.line && r.line !== '-'
        ? r.line.split('\n').map((ln) => {
          const [character, ...rest] = ln.split('：');
          return { character: character ?? '', line: rest.join('：') ?? '' };
        })
        : [],
    }));
    const blob = new Blob([JSON.stringify({ scenes }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'storyboard.json'; a.click();
    URL.revokeObjectURL(url);
  }

  // 保存データのクリア
  function clearStorage() {
    localStorage.removeItem('storyboardData');
    setItems([]);
  }

  async function submitEdits() {
    // ✅ ボタン連打・並行実行を防止
    if (editLoading || videoLoading) return;
    setEditLoading(true);
    setEditCountdown(400); // ⭐️ 追加：60秒カウント開始
    const counterStr = sessionStorage.getItem('counter');
    let counter = counterStr ? Number(counterStr) : 1;
    counter = counter + 1;
    sessionStorage.setItem('counter', String(counter));

    const payload = {
      scenes: edits.map((e) => ({
        scene_id: e.scene_id,
        fix: e.input_fix.trim() ? 'Y' : 'N', // ✅ 入力有無で判定
        input_fix: e.input_fix.trim() ? e.input_fix : '',
      })),
      project_folder: typeof window !== 'undefined' ? sessionStorage.getItem('projectFolder') : null,
      counter: String(counter),
    };

    try {
      const res = await fetch('/api/edit', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const updated = await res.json();
      applySceneJSON(updated);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      alert('送信に失敗しました: ' + msg);
    } finally {
      setEditLoading(false);
      setEditCountdown(null); // ⭐️ 追加：カウントダウンクリア
    }
  }

  async function createVideo() {
  if (videoLoading || editLoading) return; // ✅ 並行実行の抑止
  setVideoLoading(true);
  setVideoCountdown(600); // ⭐️ 600秒カウント開始

  try {
    const projectFolder =
      typeof window !== 'undefined'
        ? sessionStorage.getItem('projectFolder') ?? ""
        : "";

    const postVideo = async (num: number) => {
      const payload = { project_folder: projectFolder, num };
      const res = await fetch('/api/video', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status} @ /api/video (num=${num})`);
      return (await res.text()).trim();
    };

    // --- Step 1: num=0~3 を並列実行 ---
    const results = await Promise.all([0, 1, 2, 3].map(postVideo));

    // 全部 "success" か確認
    const failed = results
      .map((text, idx) => (text !== 'success' ? idx : -1))
      .filter((v) => v !== -1);
    if (failed.length > 0) {
      throw new Error(`Pre-steps not "success" at num=${failed.join(', ')}`);
    }

    // --- Step 2: num=4 を実行して URL を取得 ---
    const url = await postVideo(4);

    if (url && typeof window !== 'undefined') {
      try {
        sessionStorage.setItem('videoUrl', url);
      } catch {}
      router.push(`/video?src=${encodeURIComponent(url)}`);
    } else {
      alert('URLが返ってきませんでした');
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    alert('映像作成に失敗しました: ' + msg);
  } finally {
    setVideoLoading(false);
    setVideoCountdown(null); // ⭐️ カウントダウンクリア
  }
}




  const anyLoading = videoLoading || editLoading; // ✅ 共通ローディング状態

  return (
    <section className="card" style={{ position: 'relative' }}>
      <h1 style={{ marginTop: 0, color: 'var(--primary-ink)', display: 'flex', alignItems: 'center', gap: 8 }}>
        カラー絵コンテ
        {anyLoading && <span className="spinner" aria-live="polite" aria-label={videoLoading ? '映像を作成中' : '編集内容を送信中'} />}
      </h1>

      {/* ヘッダー: 列（「編集を有効化」列は削除） */}
      <div className="table-header table-grid">
        <div>シーン番号</div>
        <div>サムネイル</div>
        <div>シーン内容</div>
        <div>編集指示</div>
      </div>

      <div>
        {/* ...中略... */}
        {!loading && !err && items.map((it) => {
          const edit = edits.find((e) => e.scene_id === it.sceneId) ?? { scene_id: it.sceneId, input_fix: '' };
          return (
            <div key={it.id} className="table-row table-grid">
              {/* シーン名 */}
              <div style={{ fontWeight: 600 }}>
                <span className="muted-label"></span>
                {it.name}
              </div>

              {/* 写真 */}
              <div className="photo-frame" aria-label={`サムネイル ${it.id}`}>
                {it.photoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={it.photoUrl} alt={it.name} />
                ) : (
                  <span style={{ color: 'var(--muted)' }}>No Image</span>
                )}
              </div>

              {/* 内容 */}
              <div style={{ whiteSpace: 'pre-wrap' }}>
                <span className="muted-label"></span>
                {it.content ?? '-'}
              </div>

              {/* 編集指示 */}
              <div>
                <span className="muted-label"></span>
                <textarea
                  className="textarea"
                  placeholder="このシーンの編集指示を入力"
                  value={edit.input_fix}
                  rows={3}
                  disabled={anyLoading}
                  onChange={(e) => {
                    const v = e.target.value;
                    setEdits((prev) => prev.some((p) => p.scene_id === it.sceneId)
                      ? prev.map((p) => (p.scene_id === it.sceneId ? { ...p, input_fix: v } : p))
                      : [...prev, { scene_id: it.sceneId, input_fix: v }]
                    );
                  }}
                />
              </div>
            </div>
          );
        })}

        {/* ↓ ここにクラスを付与 */}
        <div className="table-actions" style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button
            className="btn"
            onClick={submitEdits}
            disabled={loading || anyLoading}
            aria-busy={editLoading}
          >
            {editLoading
              ? (editCountdown !== null && editCountdown > 0
                ? `編集指示を送信中…（残り約${editCountdown}秒）`
                : '編集指示を送信中… 間も無く完了')
              : '編集指示を送信'}
          </button>

          <button
            className="btn btn--primary"
            onClick={createVideo}
            disabled={anyLoading}
            aria-busy={videoLoading}
          >
            {videoLoading
              ? (videoCountdown !== null && videoCountdown > 0
                ? `映像を作成中…（残り約${videoCountdown}秒）`
                : '映像を作成中… 間も無く遷移します')
              : '映像を作成'}
          </button>

        </div>
      </div>


      {/* 画面右下に進行中インジケータ */}
      {anyLoading && (
        <div
          role="status"
          aria-live="assertive"
          style={{
            position: 'absolute',
            right: 12,
            bottom: 12,
            background: 'rgba(255,255,255,0.96)',
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
            {videoLoading ? (
              videoCountdown !== null && videoCountdown > 0
                ? `映像を作成中… 残り約${videoCountdown}秒`
                : '映像を作成中… 間も無く遷移します'
            ) : (
              editCountdown !== null && editCountdown > 0
                ? `編集内容を送信中… 残り約${editCountdown}秒`
                : '編集内容を送信中… 間も無く完了'
            )}
          </span>
        </div>
      )}

      <style jsx>{`
  /* ===== テーブルのギャップ統一 ===== */
  .card {
    /* 必要ならここで変えれば全部に反映されます */
    --cell-gap: 12px;
  }

  /* 見出し・各行とも同じカラム構成＆セル間ギャップ */
  .table-grid {
    display: grid;
    grid-template-columns: 120px 160px 1fr 1fr; /* 適宜調整 */
    column-gap: var(--cell-gap);
    align-items: start;
  }

  /* 見出しの下にセル間と同じスペース */
  .table-header {
    font-weight: 600;
    color: var(--primary-ink);
    margin-bottom: var(--cell-gap);
  }

  /* 行ごとの縦の区切りなどがあれば任意で */
  .table-row {
    padding: 8px 0; /* 任意。不要なら削除OK */
    border-top: 1px solid var(--border);
  }
  .table-row:first-of-type {
    border-top: none;
  }

  /* 「表の終わり」とボタン間のスペースをセル間と同じに */
  .table-actions {
    margin-top: var(--cell-gap);
  }

  /* シーン番号（1列目）を中央揃え */
.table-header > div:nth-child(1),
.table-row > div:nth-child(1) {
  display: flex;
  justify-content: center; /* 水平中央 */
  align-items: center;     /* 垂直中央 */
  text-align: center;
}

  /* 既存の spinner などは元のまま */
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
`}</style>

    </section>
  );
}
