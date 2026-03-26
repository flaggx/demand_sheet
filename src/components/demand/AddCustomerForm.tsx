"use client";

import { addCustomerAction, type CrudResult } from "@/app/actions/demand-crud";
import {
  CustomerChemicalsEditor,
  type ChemicalOption,
} from "@/components/demand/CustomerChemicalsEditor";
import {
  ServiceDaySelect,
  ServiceFrequencySelect,
  ServiceTechSelect,
} from "@/components/demand/ServiceEnumSelect";
import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useFormStatus } from "react-dom";

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-md bg-sky-600 px-3 py-1.5 text-sm text-white hover:bg-sky-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900 disabled:opacity-50"
    >
      {pending ? "Saving…" : label}
    </button>
  );
}

export function AddCustomerForm({
  chemicals,
  serviceDayOptions,
  serviceFrequencyOptions,
  serviceTechOptions,
}: {
  chemicals: ChemicalOption[];
  serviceDayOptions: readonly string[];
  serviceFrequencyOptions: readonly string[];
  serviceTechOptions: readonly string[];
}) {
  const router = useRouter();
  const [state, action] = useActionState(addCustomerAction, null as CrudResult | null);

  useEffect(() => {
    if (state?.ok) {
      router.push("/dashboard/demand");
    }
  }, [state, router]);

  return (
    <form action={action} className="space-y-3">
      <div>
        <label htmlFor="account_name" className="text-xs text-neutral-200">
          Account name
        </label>
        <input
          id="account_name"
          name="account_name"
          required
          className="mt-1 w-full rounded border border-neutral-500 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <ServiceDaySelect id="add_service_day" defaultValue={null} options={serviceDayOptions} />
        <ServiceFrequencySelect
          id="add_service_frequency"
          defaultValue={null}
          options={serviceFrequencyOptions}
        />
        <ServiceTechSelect id="add_service_tech" defaultValue={null} options={serviceTechOptions} />
      </div>
      <div>
        <p className="text-xs font-medium text-neutral-200">Chemicals in use</p>
        <p className="mt-1 text-xs text-neutral-300">
          Optional: check chemicals this account uses and enter quantities.
        </p>
        <div className="mt-2">
          <CustomerChemicalsEditor chemicals={chemicals} />
        </div>
      </div>
      <SubmitButton label="Add customer" />
      {state?.ok === true && (
        <p className="text-sm text-emerald-400" role="status">
          Customer added.
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
