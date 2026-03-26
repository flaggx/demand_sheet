"use client";

import {
  deleteChemicalAction,
  deleteCustomerAction,
  type CrudResult,
} from "@/app/actions/demand-crud";
import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";

export function DeleteCustomerButton({
  customerId,
  accountName,
  redirectAfter,
}: {
  customerId: string;
  accountName: string;
  /** If true, server redirects to demand list after delete (e.g. edit page). */
  redirectAfter?: boolean;
}) {
  const router = useRouter();
  const [state, action] = useActionState(deleteCustomerAction, null as CrudResult | null);

  useEffect(() => {
    if (state?.ok && !redirectAfter) {
      router.refresh();
    }
  }, [state, redirectAfter, router]);

  return (
    <div
      className={`flex flex-col gap-1 ${redirectAfter ? "items-start" : "items-end"}`}
    >
      <form
        action={action}
        onSubmit={(e) => {
          if (
            !confirm(`Delete customer "${accountName}"? This cannot be undone.`)
          ) {
            e.preventDefault();
          }
        }}
        className="inline"
      >
        <input type="hidden" name="customer_id" value={customerId} />
        {redirectAfter ? <input type="hidden" name="redirect_after" value="1" /> : null}
        <button
          type="submit"
          className="rounded-sm text-sm text-red-300 hover:text-red-200 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300 disabled:opacity-50"
        >
          Delete
        </button>
      </form>
      {state?.ok === false && (
        <span className="max-w-[12rem] text-right text-xs text-red-300">{state.error}</span>
      )}
    </div>
  );
}

export function DeleteChemicalButton({
  chemicalId,
  chemicalName,
}: {
  chemicalId: string;
  chemicalName: string;
}) {
  const router = useRouter();
  const [state, action] = useActionState(deleteChemicalAction, null as CrudResult | null);

  useEffect(() => {
    if (state?.ok) {
      router.refresh();
    }
  }, [state, router]);

  return (
    <div className="flex flex-col items-end gap-1">
      <form
        action={action}
        onSubmit={(e) => {
          if (
            !confirm(
              `Delete chemical "${chemicalName}"? Quantities for this chemical on all customers will be removed. This cannot be undone.`,
            )
          ) {
            e.preventDefault();
          }
        }}
        className="inline"
      >
        <input type="hidden" name="chemical_id" value={chemicalId} />
        <button
          type="submit"
          className="rounded-sm text-sm text-red-300 hover:text-red-200 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-300 disabled:opacity-50"
        >
          Delete
        </button>
      </form>
      {state?.ok === false && (
        <span className="max-w-[12rem] text-right text-xs text-red-300">{state.error}</span>
      )}
    </div>
  );
}
