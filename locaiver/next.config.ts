// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  eslint: {
    // 本番ビルド中は ESLint エラーで落とさない
    ignoreDuringBuilds: true,
  },
}

export default nextConfig
