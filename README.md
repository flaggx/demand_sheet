# Demand Sheet (web)

Route demand sheet web app: **Next.js** (TypeScript) with **Supabase** (planned).

## Prerequisites

- [Node.js](https://nodejs.org/) 20+ (includes `npm`)

## Setup

```bash
npm install
```

### Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Copy `.env.local.example` to `.env.local` and set **Project URL**.

**API keys (current practice)** — see [Understanding API keys](https://supabase.com/docs/guides/api/api-keys):

- **Recommended:** Dashboard → **Project Settings → API Keys** → **Publishable** key (`sb_publishable_…`) → `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- **Legacy:** **Legacy API Keys** tab → **anon** JWT → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (still supported; migrate when ready).

The app reads **publishable first**, then falls back to **anon** (`src/lib/supabase/env.ts`).

3. Restart the dev server after changing env.

**Code layout**

- `src/lib/supabase/env.ts` — URL + public key resolution.
- `src/lib/supabase/client.ts` — `createClient()` for **Client Components** (browser).
- `src/lib/supabase/server.ts` — `createClient()` for **Server Components**, Route Handlers, Server Actions.
- `middleware.ts` — refreshes the auth session cookie on each request.

Use the [Supabase Next.js guide](https://supabase.com/docs/guides/auth/server-side/nextjs) for sign-in, RLS, and policies.

### Auth (email / password)

1. In Supabase: **Authentication → Providers → Email** — enable if needed.
2. **Authentication → URL Configuration**:
   - **Site URL:** `http://localhost:3000` (add your production URL when you deploy).
   - **Redirect URLs:** include `http://localhost:3000/auth/callback` (and production callback URL later).

**Routes:** `/login` (sign in / sign up), `/auth/callback` (email confirm & OAuth PKCE), `/dashboard` (protected). Middleware redirects unauthenticated users away from `/dashboard`.

**If you see “Sign-in link expired or invalid”** after clicking the email:

1. **Redirect URLs** — In Supabase: **Authentication → URL Configuration → Redirect URLs**, add:
   - `http://localhost:3000/auth/callback`
   - `http://localhost:3000/auth/confirm` (optional alias; forwards to callback)
2. **PKCE vs email link** — `exchangeCodeForSession(code)` only works in the **same browser** where you started sign-up (PKCE cookie). Opening the link in another app/browser often fails. The callback route also supports **`token_hash` + `type`** via `verifyOtp`, which works everywhere.
3. **Confirm sign-up email template** — **Authentication → Email Templates → Confirm sign up**. Point the button at your app with `token_hash`, for example:

   ```html
   <a href="{{ .SiteURL }}/auth/callback?token_hash={{ .TokenHash }}&type=signup&next=/dashboard">Confirm your email</a>
   ```

   Use `type=recovery` for password reset, etc., per [email templates](https://supabase.com/docs/guides/auth/auth-email-templates).
4. **Corporate email** — Some providers prefetch links (e.g. Microsoft Safe Links) and burn the token; try another inbox or OTP flow from the same docs page.

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build

```bash
npm run build
npm start
```

## Legacy desktop app

The previous Python/Tkinter Windows app lives in [`deprecated/`](deprecated/).
