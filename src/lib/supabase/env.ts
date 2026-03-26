/**
 * Supabase public env — matches current Supabase guidance:
 * https://supabase.com/docs/guides/api/api-keys
 *
 * Prefer NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (sb_publishable_...).
 * Fall back to NEXT_PUBLIC_SUPABASE_ANON_KEY (legacy JWT) during migration.
 */

export function getSupabaseUrl(): string | undefined {
  return process.env.NEXT_PUBLIC_SUPABASE_URL;
}

/** Public / low-privilege key for browser and server Supabase clients. */
export function getSupabasePublicKey(): string | undefined {
  return (
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );
}

export function getSupabasePublicEnv(): { url: string; key: string } | null {
  const url = getSupabaseUrl();
  const key = getSupabasePublicKey();
  if (!url || !key) return null;
  return { url, key };
}

/** True if env looks like real keys, not template placeholders. */
export function isConfiguredSupabasePublicEnv(
  url: string | undefined,
  key: string | undefined,
): boolean {
  if (!url || !key) return false;
  if (url.includes("your-project") || url.includes("placeholder")) return false;
  if (key === "your-anon-key" || key === "your-publishable-key") return false;
  // Publishable keys: sb_publishable_...
  if (key.startsWith("sb_publishable_")) return key.length > 24;
  // Legacy anon JWT
  if (key.startsWith("eyJ")) return key.length > 40;
  return key.length >= 20;
}
