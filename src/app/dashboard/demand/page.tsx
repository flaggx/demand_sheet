import { AddChemicalForm } from "@/components/demand/AddChemicalForm";
import { AddCustomerForm } from "@/components/demand/AddCustomerForm";
import {
  DeleteChemicalButton,
  DeleteCustomerButton,
} from "@/components/demand/DemandDeleteButtons";
import { DemandImportForm } from "@/components/demand/DemandImportForm";
import { SignOutButton } from "@/components/auth/SignOutButton";
import { createClient } from "@/lib/supabase/server";
import { DEMAND_EXCEL_MAIN_SHEET } from "@/lib/demand/constants";
import { isDemandExcelImportCompleted } from "@/lib/demand/excel-import-metadata";
import Link from "next/link";
import { redirect } from "next/navigation";

export default async function DemandPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const excelImportDone = isDemandExcelImportCompleted(user);

  const [
    { count: customerCount },
    { count: chemicalCount },
    { data: chemicals },
    { data: customers },
  ] = await Promise.all([
    supabase.from("customers").select("*", { count: "exact", head: true }).eq("user_id", user.id),
    supabase.from("chemicals").select("*", { count: "exact", head: true }).eq("user_id", user.id),
    supabase
      .from("chemicals")
      .select("id, name")
      .eq("user_id", user.id)
      .order("sort_order", { ascending: true }),
    supabase
      .from("customers")
      .select("id, account_name")
      .eq("user_id", user.id)
      .order("account_name", { ascending: true }),
  ]);

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Demand</h1>
          <p className="mt-2 text-sm text-neutral-400">
            {excelImportDone
              ? "Manage customers and chemicals below."
              : `Use Import Excel once (sheet “${DEMAND_EXCEL_MAIN_SHEET}”) to load your template, then add or edit records below.`}
          </p>
          <p className="mt-3 text-sm text-neutral-500">
            <span className="text-neutral-300">{customerCount ?? 0}</span> customers ·{" "}
            <span className="text-neutral-300">{chemicalCount ?? 0}</span> chemicals
          </p>
          <p className="mt-4">
            <Link
              href="/dashboard/demand/sheet"
              className="inline-flex rounded-md bg-neutral-200 px-4 py-2 text-sm font-medium text-neutral-900 hover:bg-white"
            >
              View demand sheet (print)
            </Link>
          </p>
        </div>
        <SignOutButton />
      </div>

      <section className="mt-10 rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
        <h2 className="text-lg font-medium text-neutral-200">
          {excelImportDone ? "Re-import Excel" : "Import Excel"}
        </h2>
        <p className="mt-2 text-sm text-neutral-500">
          First row must include Account, Service Day, Service Frequency, Service Tech, then one
          column per chemical. Use “Replace all…” for a full reload from a template file.
          {excelImportDone ? " (You can re-import at any time.)" : ""}
        </p>
        <div className="mt-4">
          <DemandImportForm />
        </div>
      </section>

      <div className="mt-10 grid gap-8 sm:grid-cols-2">
        <section className="rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
          <h2 className="text-lg font-medium text-neutral-200">New customer</h2>
          <p className="mt-2 text-sm text-neutral-500">
            Add an account and optionally choose chemicals and quantities.
          </p>
          <div className="mt-4">
            <AddCustomerForm chemicals={chemicals ?? []} />
          </div>
        </section>
        <section className="rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
          <h2 className="text-lg font-medium text-neutral-200">New chemical</h2>
          <p className="mt-2 text-sm text-neutral-500">
            Adds a column to your catalog (sort order is appended).
          </p>
          <div className="mt-4">
            <AddChemicalForm />
          </div>
        </section>
      </div>

      <section className="mt-10 rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
        <h2 className="text-lg font-medium text-neutral-200">Customers</h2>
        <p className="mt-2 text-sm text-neutral-500">
          Open a customer to edit service day, frequency, tech, and chemical quantities.
        </p>
        {(customers?.length ?? 0) === 0 ? (
          <p className="mt-4 text-sm text-neutral-600">No customers yet.</p>
        ) : (
          <ul className="mt-4 divide-y divide-neutral-800 rounded border border-neutral-800">
            {customers!.map((c) => (
              <li
                key={c.id}
                className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-neutral-900/40"
              >
                <Link
                  href={`/dashboard/demand/customers/${c.id}`}
                  className="min-w-0 flex-1 text-sm text-sky-400 hover:underline"
                >
                  {c.account_name}
                </Link>
                <DeleteCustomerButton customerId={c.id} accountName={c.account_name} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-10 rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
        <h2 className="text-lg font-medium text-neutral-200">Chemical catalog</h2>
        <p className="mt-2 text-sm text-neutral-500">
          Deleting a chemical removes it from the catalog and clears its quantities for every
          customer.
        </p>
        {(chemicals?.length ?? 0) === 0 ? (
          <p className="mt-4 text-sm text-neutral-600">No chemicals yet.</p>
        ) : (
          <ul className="mt-4 divide-y divide-neutral-800 rounded border border-neutral-800">
            {chemicals!.map((ch) => (
              <li
                key={ch.id}
                className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-neutral-900/40"
              >
                <span className="min-w-0 flex-1 text-sm text-neutral-200">{ch.name}</span>
                <DeleteChemicalButton chemicalId={ch.id} chemicalName={ch.name} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
