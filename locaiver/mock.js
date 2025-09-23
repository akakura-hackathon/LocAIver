// mock.js
const express = require('express');
const cors = require('cors');

const app = express();

// JSONボディをパースする
app.use(express.json());






// CORSを許可（Next.js devサーバ: http://localhost:3000 → mock:8787 で通信できるように）
app.use(cors());

// シンプルなチャットAPI
app.post('/chat', (req, res) => {
  const msg = (req.body && req.body.message) || '';
  console.log('受信:', msg);
  res.json({ reply: `Echo: ${msg}` });
});

// サーバ起動
const port = 8787;
app.listen(port, () => {
  console.log(`Mock bot running at http://localhost:${port}`);
});
