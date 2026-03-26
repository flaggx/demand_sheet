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

      {!excelImportDone && (
        <section className="mt-10 rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
          <h2 className="text-lg font-medium text-neutral-200">Import Excel</h2>
          <p className="mt-2 text-sm text-neutral-500">
            First row must include Account, Service Day, Service Frequency, Service Tech, then one
            column per chemical. Use “Replace all…” for a full reload from a template file.
          </p>
          <div className="mt-4">
            <DemandImportForm />
          </div>
        </section>
      )}

      <div className="mt-10 grid gap-8 sm:grid-cols-2">
        <section className="rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
          <h2 className="text-lg font-medium text-neutral-200">New customer</h2>
          <p className="mt-2 text-sm text-neutral-500">
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

      <DemandSearchLists customers={customers ?? []} chemicals={chemicals ?? []} />
      {excelImportDone && (
        <section className="mt-10 rounded-lg border border-red-900/40 bg-neutral-950/50 p-6">
          <h2 className="text-lg font-medium text-neutral-200">Danger zone</h2>
          <p className="mt-2 text-sm text-neutral-500">
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
