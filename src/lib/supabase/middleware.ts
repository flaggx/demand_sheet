import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { getSupabasePublicEnv } from "./env";

/**
 * Refreshes the Supabase session and applies auth redirects for protected routes.
 * @see https://supabase.com/docs/guides/auth/server-side/nextjs
 */
export async function updateSession(request: NextRequest) {
  const env = getSupabasePublicEnv();
  if (!env) {
    return NextResponse.next({ request });
  }

  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabase = createServerClient(env.url, env.key, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet: { name: string; value: string; options?: object }[]) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        supabaseResponse = NextResponse.next({
          request,
        });
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options),
        );
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  /** Paths that must stay reachable without a session (login + OAuth/email return URLs). */
  const isPublicPath =
    pathname === "/login" ||
    pathname.startsWith("/auth/callback") ||
    pathname.startsWith("/auth/confirm");

  if (!user) {
    if (isPublicPath) {
      return supabaseResponse;
    }
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    const redirectTarget = pathname === "/" ? "/dashboard/demand" : pathname;
    url.searchParams.set("redirectTo", redirectTarget);
    return NextResponse.redirect(url);
  }

  if (user && pathname === "/login") {
    const raw = request.nextUrl.searchParams.get("redirectTo");
    const nextPath =
      raw?.startsWith("/") && !raw.startsWith("//") ? raw : "/dashboard/demand";
    const url = request.nextUrl.clone();
    url.pathname = nextPath;
    url.search = "";
    return NextResponse.redirect(url);
  }

  if (user && pathname === "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard/demand";
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}
