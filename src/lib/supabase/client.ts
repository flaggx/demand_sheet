import { createBrowserClient } from "@supabase/ssr";
import { getSupabasePublicEnv } from "./env";

/**
 * Supabase client for Client Components and browser-only code.
 * Uses publishable key (recommended) or legacy anon key — see ./env.ts
 */
export function createClient() {
  const env = getSupabasePublicEnv();
  if (!env) {
    throw new Error(
      "Missing Supabase env: set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (or legacy NEXT_PUBLIC_SUPABASE_ANON_KEY) in .env.local",
    );
  }
  return createBrowserClient(env.url, env.key);
}
