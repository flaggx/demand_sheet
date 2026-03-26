import { DeleteCustomerButton } from "@/components/demand/DemandDeleteButtons";
import { EditCustomerForm } from "@/components/demand/EditCustomerForm";
import { SignOutButton } from "@/components/auth/SignOutButton";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

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

  const [{ data: customer }, { data: chemicals }, { data: usageRows }] = await Promise.all([
    supabase
      .from("customers")
      .select("id, account_name")
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
  ]);

  if (!customer) {
    notFound();
  }

  const initialSelections: Record<string, number | null> = {};
  for (const row of usageRows ?? []) {
    initialSelections[row.chemical_id] = row.quantity;
  }

  return (
    <main className="mx-auto max-w-xl p-8">
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

      <p className="mt-8 text-sm text-neutral-500">
        <Link href="/dashboard/demand" className="text-sky-400 hover:underline">
          ← Demand data
        </Link>
      </p>
    </main>
  );
}
