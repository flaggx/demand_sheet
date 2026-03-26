import { DemandSheetPrintView } from "@/components/demand/DemandSheetPrintView";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function DemandSheetPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login");
  }

  const [{ data: chemicals }, { data: customers }] = await Promise.all([
    supabase
      .from("chemicals")
      .select("id, name, sort_order")
      .eq("user_id", user.id)
      .order("sort_order", { ascending: true }),
    supabase
      .from("customers")
      .select("id, account_name, service_day, service_frequency, service_tech")
      .eq("user_id", user.id)
      .order("account_name", { ascending: true }),
  ]);

  const customerIds = (customers ?? []).map((c) => c.id);
  let ccRows: { customer_id: string; chemical_id: string; quantity: number | null }[] = [];
  if (customerIds.length > 0) {
    const { data } = await supabase
      .from("customer_chemicals")
      .select("customer_id, chemical_id, quantity")
      .in("customer_id", customerIds);
    ccRows = data ?? [];
  }

  const byCustomer = new Map<string, Record<string, number | null>>();
  for (const id of customerIds) {
    byCustomer.set(id, {});
  }
  for (const row of ccRows) {
    const m = byCustomer.get(row.customer_id);
    if (m) {
      m[row.chemical_id] = row.quantity;
    }
  }

  const rows = (customers ?? []).map((c) => ({
    id: c.id,
    account_name: c.account_name,
    service_day: c.service_day,
    service_frequency: c.service_frequency,
    service_tech: c.service_tech,
    quantities: byCustomer.get(c.id) ?? {},
  }));

  const generatedAt = new Date().toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <DemandSheetPrintView chemicals={chemicals ?? []} rows={rows} generatedAt={generatedAt} />
  );
}
