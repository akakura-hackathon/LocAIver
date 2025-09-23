# ==== Build stage ====
FROM node:18-alpine AS builder
WORKDIR /app

## Next/SWC対策（Alpineで必要になることが多い）
RUN apk add --no-cache libc6-compat


# 依存インストール（キャッシュ効かせるために先に）
COPY package*.json ./
RUN npm ci

# ソース投入 & ビルド
COPY . .
RUN npm run build

# ==== Runtime stage ====
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=8080

## ランタイム側にも入れておくと安心
RUN apk add --no-cache libc6-compat


# standalone 出力物を配置
# これで node_modules も最小限のみ含まれる
COPY --from=builder /app/.next/standalone ./
# public と .next/static は必要
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 8080
CMD ["node", "server.js"]
