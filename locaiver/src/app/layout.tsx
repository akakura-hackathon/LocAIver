import './globals.css';

export const metadata = { title: 'LocAIver' };

// src/app/layout.tsx（ヘッダ部分のみ例）
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <header className="header">
          <nav className="nav">
            <a className="nav__logo" href="/">
              <img
                src="/demo/icon.png"
                alt="サービスアイコン"
                className="nav__logo-icon"
              />
              LocAIver
            </a>


            {/* <div className="nav__links">
              <a href="/form">初期入力フォーム</a>
              <a href="/chat">対話</a>
              <a href="/storyboard">カラー絵コンテ</a>
            </div> */}
          </nav>
        </header>
        <main className="container">{children}</main>
        <footer className="footer">© LocAIver</footer>
      </body>
    </html>
  );
}

