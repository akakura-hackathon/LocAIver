"use client";

import Link from "next/link";

export default function Page() {
  return (
    <>
      {/* Header */}
      {/* <header className="header">
        <nav className="nav">
          <Link href="/" className="nav__logo" aria-label="LocAIver ホーム">
            <span className="nav__logo-badge">L</span>
            <span>LocAIver</span>
          </Link>
          <div className="nav__links">
            <Link href="#features">特徴</Link>
            <Link href="#flow">生成の流れ</Link>
            <Link href="#usecases">ユースケース</Link>
            <Link href="/form" className="btn btn--accent" aria-label="フォームへ">
              いますぐ試す
            </Link>
          </div>
        </nav>
      </header> */}

      {/* Hero */}
      <main>
        <section className="container" aria-labelledby="hero-title">
          <div className="card" style={{ padding: 24 }}>
            <div className="row" style={{ alignItems: "center" }}>
              <div style={{ flex: 1 }}>
                <h1
                  id="hero-title"
                  style={{
                    margin: "0 0 8px",
                    color: "var(--primary-ink)",
                    fontSize: "clamp(24px,3.6vw,40px)",
                    lineHeight: 1.2,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25em" // テキストと画像の間に少し余白
                  }}
                >
                  <img
                    src="/demo/icon.png"
                    alt="サービスアイコン"
                    style={{ height: "1em", width: "auto" }}
                  />
                  LocAIver
                </h1>

                <p style={{ margin: "0 0 14px", fontSize: "clamp(14px,2.2vw,18px)", color: "var(--muted)" }}>
                  <div>Local + AI + Deliver = <strong>LocAIver</strong></div>
                  <div>映像制作の経験がなくても、</div>
                  <div><strong>対話 → カラー絵コンテ案 → 編集 → 完成</strong></div>
                  <div>のシンプルな流れで、</div>
                  地域の魅力を動画にして届けます。
                </p>
                <div className="row" style={{ alignItems: "center" }}>
                  <Link href="/form" className="btn" aria-label="フォームへ進む">
                    映像作成を開始する
                  </Link>
                  <a href="#features" className="btn btn--ghost" aria-label="特徴へ移動">
                    概要を確認する
                  </a>
                </div>
              </div>

              {/* Visual */}
              <div className="card" style={{ flex: 1, minWidth: 260 }} aria-hidden>
                <div className="row" style={{ gap: 10, alignItems: "center" }}>
                  <div className="photo-frame">
                    <img src="/demo/market.png" alt="特産物の紹介イメージ" />
                  </div>
                  <div className="photo-frame">
                    <img src="/demo/craft.png" alt="伝統工芸の紹介イメージ" />
                  </div>
                  <div className="photo-frame">
                    <img src="/demo/furusato.png" alt="ふるさと納税イメージ" />
                  </div>
                </div>
                <div className="separator" style={{ marginTop: 12 }}>地域の魅力を、だれでも。</div>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>
                  画像はイメージです。AIが質問に沿って素材・構成案を作ります。
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="container">
          <div className="features-row">  {/* ← row を使わない */}
            <article className="card">
              <h2 style={{ marginTop: 0, fontSize: 18 }}>だれでも、直感的</h2>
              <p style={{ marginTop: 6 }}>
                専門知識や複雑な指示は不要。AIが質問を投げかけ、要点を引き出して構成します。
              </p>
            </article>
            <article className="card">
              <h2 style={{ marginTop: 0, fontSize: 18 }}>低コスト & 速い</h2>
              <p style={{ marginTop: 6 }}>
                外注のやり取りや待ち時間を削減。試作～編集もその場で行えるので、完成までの時間も短縮。
              </p>
            </article>
            <article className="card">
              <h2 style={{ marginTop: 0, fontSize: 18 }}>ギャップを防ぐ</h2>
              <p style={{ marginTop: 6 }}>
                カラー絵コンテ案 → 編集 → カラー絵コンテ再提案をインタラクティブに繰り返し、「思っていたものと違う」を解消。
              </p>
            </article>
          </div>
        </section>

        {/* Flow */}
        <section id="flow" className="container">
          <div className="card" style={{ padding: 20}}>
            <h2 style={{ marginTop: 0 }}>生成の流れ</h2>
            <div className="table-header" role="row" style={{marginBottom: "10px"}}>
              <div>ステップ</div>
              <div>イメージ</div>
              <div>内容</div>
              {/* <div>出力</div> */}
            </div>

            <div className="table-row" role="row">
              <div>
                <strong>1. 対話</strong>
                <div className="muted-label">ヒアリング</div>
              </div>
              <div>
                <div className="photo-frame"><img src="/demo/chat.png" alt="対話" /></div>
              </div>
              <div>
                PR対象・雰囲気・尺・入れたい素材などを AI が丁寧に質問。
              </div>
              {/* <div>要件サマリ</div> */}
            </div>

            <div className="table-row" role="row">
              <div>
                <strong>2. カラー絵コンテ案</strong>
                <div className="muted-label">構成の見える化</div>
              </div>
              <div>
                <div className="photo-frame"><img src="/demo/board.png" alt="カラー絵コンテ案" /></div>
              </div>
              <div>
                AIがストリーをシーンに分割し、シーンの内容と代表画像を自動生成。
              </div>
              {/* <div>絵コンテ / 台本ドラフト</div> */}
            </div>

            <div className="table-row" role="row">
              <div>
                <strong>3. 編集</strong>
                <div className="muted-label">即時反映</div>
              </div>
              <div>
                <div className="photo-frame"><img src="/demo/revise.png" alt="編集" /></div>
              </div>
              <div>
                編集指示によって、AIがカラー絵コンテを再提案。
              </div>
              {/* <div>改訂版コンテ</div> */}
            </div>

            <div className="table-row" role="row">
              <div>
                <strong>4. 完成</strong>
                <div className="muted-label">書き出し</div>
              </div>
              <div>
                <div className="photo-frame"><img src="/demo/export.png" alt="完成動画" /></div>
              </div>
              <div>
                カラー絵コンテをもとに、地方PR映像が完成。
              </div>
              {/* <div>動画ファイル / サムネイル</div> */}
            </div>

            <div className="row" style={{ justifyContent: "flex-end", marginTop: 12 }}>
              <Link href="/form" className="btn" aria-label="フォームへ">
                実際に映像を作成する
              </Link>
            </div>
          </div>
        </section>

        {/* Use cases */}
        <section id="usecases" className="container">
          <div className="card" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div>
              <h2 style={{ marginTop: 0 }}>主なユースケース</h2>
              <ul style={{ marginTop: 8, lineHeight: 1.9 }}>
                <li>ふるさと納税返礼品のPR</li>
                <li>地域特産物・食材のプロモーション</li>
                <li>伝統工芸・文化財の紹介映像</li>
                <li>観光スポットのショート動画（SNS対応）</li>
                <li>移住・定住促進のプロモーション</li>
              </ul>
            </div>
            <div>
              <div className="video-slot">
                <div className="phone-frame">
                  <video
                    src="/videos/sample1.mp4"
                    controls
                    playsInline
                    preload="metadata"
                    style={{ width: "100%", height: "100%", objectFit: "contain" }}
                  >
                    お使いのブラウザは動画の再生に対応していません。
                  </video>
                </div>

                <style jsx>{`
    .video-slot {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      padding: 24px;
      background: var(--background, #f8f8f8);
    }

    /* 横長のプレビュー枠（16:9） */
    .landscape-frame {
      aspect-ratio: 16 / 9;
      width: 100%;
      max-width: 880px;        /* レイアウトに合わせて調整 */
      background: #000;        /* 左右ピラーボックスが黒で見える */
      border-radius: 16px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.2);
      overflow: hidden;

      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* 縦動画を横枠の中で中央に等倍表示（左右に余白） */
    .landscape-frame video {
      width: 640px;      /* 固定 */
      height: 360px;
      height: 100%;     /* 縦方向を枠いっぱいに */
      width: auto;      /* 比率を維持して横は自動 */
      display: block;
      object-fit: contain;   /* 念のため（効いても悪さしません） */
    }

    /* 画面がとても狭い時は枠の最大幅を少し抑制（任意） */
    @media (max-width: 360px) {
      .landscape-frame {
        max-width: 320px;
      }
    }
  `}</style>
              </div>

            </div>
          </div>
        </section>
      </main >
      {/* <footer className="footer">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>© {new Date().getFullYear()} LocAIver</div>
          <div>
            <Link href="/form">生成フォーム</Link>
            <span style={{ margin: "0 8px", color: "var(--border)" }}>|</span>
            <a href="#top">トップ</a>
          </div>
        </div>
      </footer> */}
    </>
  );
}
