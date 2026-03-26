import { AddChemicalForm } from "@/components/demand/AddChemicalForm";
import { AddCustomerForm } from "@/components/demand/AddCustomerForm";
import { DemandSearchLists } from "@/components/demand/DemandSearchLists";
import { DemandImportForm } from "@/components/demand/DemandImportForm";
import { SignOutButton } from "@/components/auth/SignOutButton";
import { createClient } from "@/lib/supabase/server";
import { DEMAND_EXCEL_MAIN_SHEET } from "@/lib/demand/constants";
import { isDemandExcelImportCompleted } from "@/lib/demand/excel-import-metadata";
import Link from "next/link";
import { redirect } from "next/navigation";

function uniqueNonEmpty(values: (string | null)[]): string[] {
  return [...new Set(values.map((v) => (v ?? "").trim()).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b),
  );
}

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
      .select("id, account_name, service_day, service_frequency, service_tech")
      .eq("user_id", user.id)
      .order("account_name", { ascending: true }),
  ]);

  const serviceDayOptions = uniqueNonEmpty((customers ?? []).map((c) => c.service_day));
  const serviceFrequencyOptions = uniqueNonEmpty(
    (customers ?? []).map((c) => c.service_frequency),
  );
  const serviceTechOptions = uniqueNonEmpty((customers ?? []).map((c) => c.service_tech));

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Demand</h1>
          <p className="mt-2 text-sm text-neutral-200">
            {excelImportDone
              ? "Manage customers and chemicals below."
              : `Use Import Excel once (sheet “${DEMAND_EXCEL_MAIN_SHEET}”) to load your template, then add or edit records below.`}
          </p>
          <p className="mt-3 text-sm text-neutral-300">
            <span className="text-neutral-100">{customerCount ?? 0}</span> customers ·{" "}
            <span className="text-neutral-100">{chemicalCount ?? 0}</span> chemicals
          </p>
          <p className="mt-4">
            <Link
              href="/dashboard/demand/sheet"
              className="inline-flex rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-white hover:bg-sky-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900"
            >
              View demand sheet (print)
            </Link>
          </p>
        </div>
        <SignOutButton />
      </div>

      {!excelImportDone && (
        <section className="mt-10 rounded-lg border border-neutral-700 bg-neutral-900/70 p-6">
          <h2 className="text-lg font-medium text-neutral-200">Import Excel</h2>
          <p className="mt-2 text-sm text-neutral-300">
            First row must include Account, Service Day, Service Frequency, Service Tech, then one
            column per chemical. Use “Replace all…” for a full reload from a template file.
          </p>
          <div className="mt-4">
            <DemandImportForm />
          </div>
        </section>
      )}

      <div className="mt-10 grid gap-8 sm:grid-cols-2">
        <section className="rounded-lg border border-neutral-700 bg-neutral-900/70 p-6">
          <h2 className="text-lg font-medium text-neutral-200">New customer</h2>
          <p className="mt-2 text-sm text-neutral-300">
            Add an account and optionally choose chemicals and quantities.
          </p>
          <div className="mt-4">
            <AddCustomerForm
              chemicals={chemicals ?? []}
              serviceDayOptions={serviceDayOptions}
              serviceFrequencyOptions={serviceFrequencyOptions}
              serviceTechOptions={serviceTechOptions}
            />
          </div>
        </section>
        <section className="rounded-lg border border-neutral-700 bg-neutral-900/70 p-6">
          <h2 className="text-lg font-medium text-neutral-200">New chemical</h2>
          <p className="mt-2 text-sm text-neutral-300">
            Adds a column to your catalog (sort order is appended).
          </p>
          <div className="mt-4">
            <AddChemicalForm />
          </div>
        </section>
      </div>

      <DemandSearchLists customers={customers ?? []} chemicals={chemicals ?? []} />
      {excelImportDone && (
        <section className="mt-10 rounded-lg border border-red-700/60 bg-neutral-900/70 p-6">
          <h2 className="text-lg font-medium text-neutral-200">Danger zone</h2>
          <p className="mt-2 text-sm text-neutral-200">
            Re-importing can overwrite existing demand data when you choose Replace all.
          </p>
          <div className="mt-4">
            <DemandImportForm />
          </div>
        </section>
      )}
    </main>
  );
}
