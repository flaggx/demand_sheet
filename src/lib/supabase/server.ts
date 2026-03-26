import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { getSupabasePublicEnv } from "./env";

/**
 * Supabase client for Server Components, Route Handlers, and Server Actions.
 * Respects the user session via cookies (refreshed by middleware).
 */
export async function createClient() {
  const env = getSupabasePublicEnv();
  if (!env) {
    throw new Error(
      "Missing Supabase env: set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (or legacy NEXT_PUBLIC_SUPABASE_ANON_KEY) in .env.local",
    );
  }

  const cookieStore = await cookies();

  return createServerClient(
    env.url,
    env.key,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet: { name: string; value: string; options?: object }[]) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Called from a Server Component — middleware will refresh the session.
          }
        },
      },
    },
  );
}
