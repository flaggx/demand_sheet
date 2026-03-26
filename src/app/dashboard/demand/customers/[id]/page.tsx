import { DeleteCustomerButton } from "@/components/demand/DemandDeleteButtons";
import { EditCustomerForm } from "@/components/demand/EditCustomerForm";
import { SignOutButton } from "@/components/auth/SignOutButton";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

function uniqueNonEmpty(values: (string | null)[]): string[] {
  return [...new Set(values.map((v) => (v ?? "").trim()).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b),
  );
}

type Props = {
  params: Promise<{ id: string }>;
};

export default async function EditCustomerPage({ params }: Props) {
  const { id: customerId } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const [{ data: customer }, { data: chemicals }, { data: usageRows }, { data: serviceRows }] =
    await Promise.all([
    supabase
      .from("customers")
      .select("id, account_name, service_day, service_frequency, service_tech")
      .eq("id", customerId)
      .eq("user_id", user.id)
      .maybeSingle(),
    supabase
      .from("chemicals")
      .select("id, name")
      .eq("user_id", user.id)
      .order("sort_order", { ascending: true }),
    supabase
      .from("customer_chemicals")
      .select("chemical_id, quantity")
      .eq("customer_id", customerId),
    supabase
      .from("customers")
      .select("service_day, service_frequency, service_tech")
      .eq("user_id", user.id),
    ]);

  if (!customer) {
    notFound();
  }

  const initialSelections: Record<string, number | null> = {};
  for (const row of usageRows ?? []) {
    initialSelections[row.chemical_id] = row.quantity;
  }
  const serviceDayOptions = uniqueNonEmpty((serviceRows ?? []).map((row) => row.service_day));
  const serviceFrequencyOptions = uniqueNonEmpty(
    (serviceRows ?? []).map((row) => row.service_frequency),
  );
  const serviceTechOptions = uniqueNonEmpty((serviceRows ?? []).map((row) => row.service_tech));

  return (
    <main className="mx-auto max-w-xl p-8">
      <p>
        <Link
          href="/dashboard/demand"
          className="inline-flex items-center rounded-md border border-neutral-700 bg-neutral-900 px-3 py-1.5 text-sm text-neutral-200 hover:bg-neutral-800"
        >
          ← Back to demand data
        </Link>
      </p>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Edit customer</h1>
          <p className="mt-2 text-sm text-neutral-400">{customer.account_name}</p>
        </div>
        <SignOutButton />
      </div>

      <section className="mt-8 rounded-lg border border-neutral-800 bg-neutral-950/50 p-6">
        <EditCustomerForm
          customerId={customer.id}
          accountName={customer.account_name}
          serviceDay={customer.service_day}
          serviceFrequency={customer.service_frequency}
          serviceTech={customer.service_tech}
          serviceDayOptions={serviceDayOptions}
          serviceFrequencyOptions={serviceFrequencyOptions}
          serviceTechOptions={serviceTechOptions}
          chemicals={chemicals ?? []}
          initialSelections={initialSelections}
        />
      </section>

      <section className="mt-6 rounded-lg border border-red-900/40 bg-neutral-950/50 p-6">
        <h2 className="text-sm font-medium text-neutral-400">Danger zone</h2>
        <p className="mt-2 text-sm text-neutral-500">
          Permanently delete this customer and their chemical quantities.
        </p>
        <div className="mt-3">
          <DeleteCustomerButton
            customerId={customer.id}
            accountName={customer.account_name}
            redirectAfter
          />
        </div>
      </section>

    </main>
  );
}
