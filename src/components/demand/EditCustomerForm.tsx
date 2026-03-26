"use client";

import { updateCustomerAction, type CrudResult } from "@/app/actions/demand-crud";
import { useActionState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useFormStatus } from "react-dom";
import {
  CustomerChemicalsEditor,
  type ChemicalOption,
} from "@/components/demand/CustomerChemicalsEditor";
import {
  ServiceDaySelect,
  ServiceFrequencySelect,
  ServiceTechSelect,
} from "@/components/demand/ServiceEnumSelect";

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900 disabled:opacity-50"
    >
      {pending ? "Saving…" : label}
    </button>
  );
}

export type EditCustomerFormProps = {
  customerId: string;
  accountName: string;
  serviceDay: string | null;
  serviceFrequency: string | null;
  serviceTech: string | null;
  serviceDayOptions: readonly string[];
  serviceFrequencyOptions: readonly string[];
  serviceTechOptions: readonly string[];
  chemicals: ChemicalOption[];
  /** chemical id → quantity for chemicals this customer uses */
  initialSelections: Record<string, number | null>;
};

export function EditCustomerForm({
  customerId,
  accountName,
  serviceDay,
  serviceFrequency,
  serviceTech,
  serviceDayOptions,
  serviceFrequencyOptions,
  serviceTechOptions,
  chemicals,
  initialSelections,
}: EditCustomerFormProps) {
  const router = useRouter();
  const [state, action] = useActionState(updateCustomerAction, null as CrudResult | null);

  useEffect(() => {
    if (state?.ok) {
      router.push("/dashboard/demand");
    }
  }, [state, router]);

  return (
    <form action={action} className="space-y-4">
      <input type="hidden" name="customer_id" value={customerId} />
      <div>
        <label htmlFor="edit_account_name" className="text-xs text-neutral-200">
          Account name
        </label>
        <input
          id="edit_account_name"
          name="account_name"
          required
          defaultValue={accountName}
          className="mt-1 w-full rounded border border-neutral-500 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900"
        />
      </div>
      <div>
        <p className="text-xs text-neutral-200">
          Service values are pre-filled from the customer row; update as needed.
        </p>
        <div className="mt-2 grid gap-3 sm:grid-cols-3">
          <ServiceDaySelect
            id="edit_service_day"
            defaultValue={serviceDay}
            options={serviceDayOptions}
            required
          />
          <ServiceFrequencySelect
            id="edit_service_frequency"
            defaultValue={serviceFrequency}
            label="Service frequency"
            options={serviceFrequencyOptions}
            required
          />
          <ServiceTechSelect
            id="edit_service_tech"
            defaultValue={serviceTech}
            label="Service tech"
            options={serviceTechOptions}
            required
          />
        </div>
      </div>
      <div>
        <p className="text-xs font-medium text-neutral-200">Chemical usage</p>
        <p className="mt-1 text-xs text-neutral-300">
          Check chemicals this account uses and set quantities. Saving replaces previous usage for
          this customer.
        </p>
        <div className="mt-2">
          <CustomerChemicalsEditor
            chemicals={chemicals}
            initialSelections={initialSelections}
          />
        </div>
      </div>
      <SubmitButton label="Save changes" />
      {state?.ok === true && (
        <p className="text-sm text-emerald-400" role="status">
          Saved.
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
