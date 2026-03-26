"use client";

import { importDemandExcelAction, type ImportDemandResult } from "@/app/actions/demand-import";
import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useFormStatus } from "react-dom";

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900 disabled:opacity-50"
    >
      {pending ? "Importing…" : label}
    </button>
  );
}

export function DemandImportForm() {
  const router = useRouter();
  const [state, action] = useActionState(
    importDemandExcelAction,
    null as ImportDemandResult | null,
  );

  useEffect(() => {
    if (state?.ok) {
      router.refresh();
    }
  }, [state, router]);

  return (
    <form action={action} className="space-y-4">
      <div>
        <label htmlFor="demand-file" className="block text-sm font-medium text-neutral-200">
          Excel file (.xlsx)
        </label>
        <input
          id="demand-file"
          name="file"
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          required
          className="mt-2 block w-full text-sm text-neutral-200 outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900 file:mr-3 file:rounded file:border-0 file:bg-neutral-700 file:px-3 file:py-2 file:text-neutral-100"
        />
      </div>
      <label className="flex items-center gap-2 text-sm text-neutral-200">
        <input
          type="checkbox"
          name="replace"
          value="true"
          className="rounded border-neutral-500 focus-visible:ring-2 focus-visible:ring-sky-400"
        />
        Replace all existing customers and chemicals for my account before
        importing
      </label>
      <SubmitButton label="Import" />
      {state?.ok === true && (
        <p className="text-sm text-emerald-400" role="status">
          Imported sheet “{state.sheetName}”: {state.customersImported} customers,{" "}
          {state.chemicalsCount} chemical columns.
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
