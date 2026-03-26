import { createClient } from "@/lib/supabase/server";
import type { EmailOtpType } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

function safeNextPath(next: string | null) {
  if (next?.startsWith("/") && !next.startsWith("//")) return next;
  return "/dashboard/demand";
}

/**
 * Auth return URL — handles:
 * - **token_hash + type** (email confirm / magic link / recovery) via `verifyOtp` — works in any browser
 * - **code** (OAuth / PKCE) via `exchangeCodeForSession` — needs PKCE cookies from same browser
 *
 * @see https://supabase.com/docs/guides/auth/passwords#signing-up-with-an-email-and-password
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const next = safeNextPath(searchParams.get("next"));
  const token_hash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;
  const code = searchParams.get("code");

  const supabase = await createClient();

  if (token_hash && type) {
    const { error } = await supabase.auth.verifyOtp({ type, token_hash });
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/login?error=auth`);
}
