"use client";

import { addChemicalAction, type CrudResult } from "@/app/actions/demand-crud";
import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useFormStatus } from "react-dom";

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-md bg-neutral-700 px-3 py-1.5 text-sm text-neutral-100 hover:bg-neutral-600 disabled:opacity-50"
    >
      {pending ? "Saving…" : label}
    </button>
  );
}

export function AddChemicalForm() {
  const router = useRouter();
  const [state, action] = useActionState(addChemicalAction, null as CrudResult | null);

  useEffect(() => {
    if (state?.ok) {
      router.refresh();
    }
  }, [state, router]);

  return (
    <form action={action} className="space-y-3">
      <div>
        <label htmlFor="chem_name" className="text-xs text-neutral-500">
          Chemical name
        </label>
        <input
          id="chem_name"
          name="name"
          required
          className="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-200"
        />
      </div>
      <SubmitButton label="Add chemical" />
      {state?.ok === true && (
        <p className="text-sm text-emerald-400" role="status">
          Chemical added.
        </p>
      )}
      {state?.ok === false && (
        <p className="text-sm text-red-400" role="alert">
          {state.error}
        </p>
      )}
    </form>
  );
}
