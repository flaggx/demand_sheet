import {
  getSupabasePublicKey,
  getSupabaseUrl,
  isConfiguredSupabasePublicEnv,
} from "@/lib/supabase/env";

/**
 * Server component: shows whether Supabase env is configured (no secrets exposed).
 */
export function SupabaseSetupHint() {
  const url = getSupabaseUrl();
  const key = getSupabasePublicKey();
  const configured = isConfiguredSupabasePublicEnv(url, key);

  if (configured) {
    return (
      <p className="mt-4 text-sm text-emerald-500/90">
        Supabase env detected — you can use `createClient()` from server or client
        utilities.
      </p>
    );
  }

  return (
    <div className="mt-6 max-w-md rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 text-left text-sm text-neutral-300">
      <p className="font-medium text-amber-200/90">Next: connect Supabase</p>
      <ol className="mt-2 list-decimal space-y-1 pl-5 text-neutral-400">
        <li>Create a project at supabase.com</li>
        <li>
          Dashboard → <strong>Project Settings</strong> → <strong>API Keys</strong>: copy
          the <strong>Publishable</strong> key (<code className="text-neutral-500">sb_publishable_…</code>)
        </li>
        <li>
          Same page: copy <strong>Project URL</strong> (or use the Connect dialog)
        </li>
        <li>
          Put them in <code className="text-neutral-500">.env.local</code> — see{" "}
          <code className="text-neutral-500">.env.local.example</code>
        </li>
        <li>
          Legacy <strong>anon</strong> JWT still works via{" "}
          <code className="text-neutral-500">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> if you
          prefer not to migrate yet
        </li>
        <li>Restart `npm run dev`</li>
      </ol>
      <p className="mt-3 text-xs text-neutral-500">
        Docs:{" "}
        <a
          className="text-sky-400 underline"
          href="https://supabase.com/docs/guides/api/api-keys"
          target="_blank"
          rel="noreferrer"
        >
          Understanding API keys
        </a>
      </p>
    </div>
  );
}
