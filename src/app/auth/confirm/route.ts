import { NextResponse } from "next/server";

/**
 * Supabase docs use `/auth/confirm` for token_hash; we handle auth in `/auth/callback`.
 * This forwards so either URL works with the same Redirect URL allowlist.
 */
export async function GET(request: Request) {
  const url = new URL(request.url);
  url.pathname = "/auth/callback";
  return NextResponse.redirect(url.toString());
}
