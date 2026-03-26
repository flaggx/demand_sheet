import { LoginForm } from "@/components/auth/LoginForm";
import { Suspense } from "react";

function LoginFormFallback() {
  return (
    <div className="mx-auto h-64 max-w-sm animate-pulse rounded-lg border border-neutral-800 bg-neutral-950/80" />
  );
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Sign in to access the app. Accounts are not created from this screen.
        </p>
      </div>
      {error === "auth" && (
        <p
          className="mb-4 max-w-sm text-center text-sm text-red-400"
          role="alert"
        >
          Sign-in link expired or invalid. Try again.
        </p>
      )}
      <Suspense fallback={<LoginFormFallback />}>
        <LoginForm />
      </Suspense>
      <p className="mt-8 text-sm text-neutral-600">
        Need access? Ask whoever manages your Supabase project to create a user for you.
      </p>
    </main>
  );
}
