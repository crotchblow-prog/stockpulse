import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      // Defensive permanent redirects for users with bookmarks to the
      // pre-cutover Phase 1 URL space. Phase 1 archive lives at
      // /legacy/archive post-M4. Without these, bookmarked /archive
      // links 404 silently.
      { source: "/archive", destination: "/legacy/archive", permanent: true },
      { source: "/archive/:date", destination: "/legacy/archive/:date", permanent: true },
      { source: "/zh/archive", destination: "/legacy/zh/archive", permanent: true },
      { source: "/zh/archive/:date", destination: "/legacy/zh/archive/:date", permanent: true },
    ];
  },
};

export default nextConfig;
