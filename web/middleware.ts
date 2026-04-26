import { NextResponse, type NextRequest } from "next/server";

/**
 * Basic-auth gate scoped to `/v2/*` only. Active during M1-M3 to keep WIP hidden
 * from share-link readers. M4's cutover step will remove this when /v2 → /.
 *
 * Public routes (/, /zh, /archive, /learn, /zh/learn, etc.) are NOT gated.
 *
 * If BASIC_AUTH_USER or BASIC_AUTH_PASS are missing in the runtime env, the
 * gate is open (returns next()) — fail-open so a misconfigured deploy doesn't
 * 401 the WIP into a black box. Configure via Vercel env vars + .env.local.
 */
export function middleware(req: NextRequest) {
  const user = process.env.BASIC_AUTH_USER;
  const pass = process.env.BASIC_AUTH_PASS;

  if (!user || !pass) {
    return NextResponse.next();
  }

  const authHeader = req.headers.get("authorization");
  if (authHeader?.startsWith("Basic ")) {
    const encoded = authHeader.slice("Basic ".length);
    const decoded = atob(encoded);
    const sep = decoded.indexOf(":");
    if (sep !== -1) {
      const u = decoded.slice(0, sep);
      const p = decoded.slice(sep + 1);
      if (u === user && p === pass) {
        return NextResponse.next();
      }
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="VIXPulse v2 preview", charset="UTF-8"',
    },
  });
}

export const config = {
  matcher: ["/v2/:path*"],
};
