"use server";

import { createClient } from "@/lib/supabase/server";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export type CrudResult = { ok: true } | { ok: false; error: string };

function resolveFormData(a: CrudResult | null | FormData, b?: FormData): FormData | null {
  if (b instanceof FormData) return b;
  if (a instanceof FormData) return a;
  return null;
}

function emptyToNull(value: FormDataEntryValue | null): string | null {
  if (value === null || value === undefined) return null;
  const s = String(value).trim();
  return s === "" ? null : s;
}

export async function addCustomerAction(
  a: CrudResult | null | FormData,
  b?: FormData,
): Promise<CrudResult> {
  const formData = resolveFormData(a, b);
  if (!formData) {
    return { ok: false, error: "Invalid form submission." };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { ok: false, error: "Not signed in." };
  }

  const account_name = String(formData.get("account_name") ?? "").trim();
  if (!account_name) {
    return { ok: false, error: "Account name is required." };
  }

  const service_day = emptyToNull(formData.get("service_day"));
  const service_frequency = emptyToNull(formData.get("service_frequency"));
  const service_tech = emptyToNull(formData.get("service_tech"));

  const { data: allowedChems, error: chemListErr } = await supabase
    .from("chemicals")
    .select("id")
    .eq("user_id", user.id);

  if (chemListErr) {
    return { ok: false, error: chemListErr.message };
  }

  const allowedIds = new Set((allowedChems ?? []).map((c) => c.id));
  const ccRows = getChemicalRowsFromForm(formData, allowedIds);

  const { data: inserted, error } = await supabase
    .from("customers")
    .insert({
      user_id: user.id,
      account_name,
      service_day,
      service_frequency,
      service_tech,
    })
    .select("id")
    .single();

  if (error) {
    if (error.code === "23505") {
      return { ok: false, error: "A customer with that account name already exists." };
    }
    return { ok: false, error: error.message };
  }

  if (ccRows.length > 0 && inserted) {
    const { error: ccErr } = await supabase.from("customer_chemicals").insert(
      ccRows.map((r) => ({
        customer_id: inserted.id,
        chemical_id: r.chemical_id,
        quantity: r.quantity,
      })),
    );
    if (ccErr) {
      return { ok: false, error: ccErr.message };
    }
  }

  return { ok: true };
}

export async function updateCustomerAction(
  a: CrudResult | null | FormData,
  b?: FormData,
): Promise<CrudResult> {
  const formData = resolveFormData(a, b);
  if (!formData) {
    return { ok: false, error: "Invalid form submission." };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { ok: false, error: "Not signed in." };
  }

  const customerId = String(formData.get("customer_id") ?? "").trim();
  if (!customerId) {
    return { ok: false, error: "Missing customer." };
  }

  const { data: existing, error: fetchErr } = await supabase
    .from("customers")
    .select("id")
    .eq("id", customerId)
    .eq("user_id", user.id)
    .maybeSingle();

  if (fetchErr) {
    return { ok: false, error: fetchErr.message };
  }
  if (!existing) {
    return { ok: false, error: "Customer not found." };
  }

  const account_name = String(formData.get("account_name") ?? "").trim();
  if (!account_name) {
    return { ok: false, error: "Account name is required." };
  }

  const service_day = emptyToNull(formData.get("service_day"));
  const service_frequency = emptyToNull(formData.get("service_frequency"));
  const service_tech = emptyToNull(formData.get("service_tech"));

  if (!service_day || !service_frequency || !service_tech) {
    return {
      ok: false,
      error: "Select service day, service frequency, and service tech.",
    };
  }

  const { error: updErr } = await supabase
    .from("customers")
    .update({
      account_name,
      service_day,
      service_frequency,
      service_tech,
      updated_at: new Date().toISOString(),
    })
    .eq("id", customerId)
    .eq("user_id", user.id);

  if (updErr) {
    if (updErr.code === "23505") {
      return { ok: false, error: "A customer with that account name already exists." };
    }
    return { ok: false, error: updErr.message };
  }

  const { data: allowedChems, error: chemListErr } = await supabase
    .from("chemicals")
    .select("id")
    .eq("user_id", user.id);

  if (chemListErr) {
    return { ok: false, error: chemListErr.message };
  }

  const allowedIds = new Set((allowedChems ?? []).map((c) => c.id));
  const ccRows = getChemicalRowsFromForm(formData, allowedIds);

  const { error: delErr } = await supabase
    .from("customer_chemicals")
    .delete()
    .eq("customer_id", customerId);

  if (delErr) {
    return { ok: false, error: delErr.message };
  }

  if (ccRows.length > 0) {
    const { error: insErr } = await supabase.from("customer_chemicals").insert(
      ccRows.map((r) => ({
        customer_id: customerId,
        chemical_id: r.chemical_id,
        quantity: r.quantity,
      })),
    );
    if (insErr) {
      return { ok: false, error: insErr.message };
    }
  }

  return { ok: true };
}

export async function addChemicalAction(
  a: CrudResult | null | FormData,
  b?: FormData,
): Promise<CrudResult> {
  const formData = resolveFormData(a, b);
  if (!formData) {
    return { ok: false, error: "Invalid form submission." };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { ok: false, error: "Not signed in." };
  }

  const name = String(formData.get("name") ?? "").trim();
  if (!name) {
    return { ok: false, error: "Chemical name is required." };
  }

  const { data: last } = await supabase
    .from("chemicals")
    .select("sort_order")
    .eq("user_id", user.id)
    .order("sort_order", { ascending: false })
    .limit(1)
    .maybeSingle();

  const sort_order = (last?.sort_order ?? -1) + 1;

  const { error } = await supabase.from("chemicals").insert({
    user_id: user.id,
    name,
    sort_order,
  });

  if (error) {
    if (error.code === "23505") {
      return { ok: false, error: "A chemical with that name already exists." };
    }
    return { ok: false, error: error.message };
  }

  return { ok: true };
}

export async function deleteCustomerAction(
  a: CrudResult | null | FormData,
  b?: FormData,
): Promise<CrudResult> {
  const formData = resolveFormData(a, b);
  if (!formData) {
    return { ok: false, error: "Invalid form submission." };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { ok: false, error: "Not signed in." };
  }

  const customerId = String(formData.get("customer_id") ?? "").trim();
  if (!customerId) {
    return { ok: false, error: "Missing customer." };
  }

  const { error } = await supabase
    .from("customers")
    .delete()
    .eq("id", customerId)
    .eq("user_id", user.id);

  if (error) {
    return { ok: false, error: error.message };
  }

  revalidatePath("/dashboard/demand");
  revalidatePath("/dashboard/demand/sheet");

  if (formData.get("redirect_after") === "1") {
    redirect("/dashboard/demand");
  }

  return { ok: true };
}

export async function deleteChemicalAction(
  a: CrudResult | null | FormData,
  b?: FormData,
): Promise<CrudResult> {
  const formData = resolveFormData(a, b);
  if (!formData) {
    return { ok: false, error: "Invalid form submission." };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { ok: false, error: "Not signed in." };
  }

  const chemicalId = String(formData.get("chemical_id") ?? "").trim();
  if (!chemicalId) {
    return { ok: false, error: "Missing chemical." };
  }

  const { error } = await supabase
    .from("chemicals")
    .delete()
    .eq("id", chemicalId)
    .eq("user_id", user.id);

  if (error) {
    return { ok: false, error: error.message };
  }

  revalidatePath("/dashboard/demand");
  revalidatePath("/dashboard/demand/sheet");

  return { ok: true };
}

function parseQuantityFromForm(raw: FormDataEntryValue | null): number | null {
  if (raw === null || raw === "") return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

function getChemicalRowsFromForm(
  formData: FormData,
  allowedIds: Set<string>,
): { chemical_id: string; quantity: number | null }[] {
  const useIds = formData.getAll("chemical_use").map(String);
  const rows: { chemical_id: string; quantity: number | null }[] = [];
  for (const chemicalId of useIds) {
    if (!allowedIds.has(chemicalId)) continue;
    const raw = formData.get(`qty_${chemicalId}`);
    rows.push({ chemical_id: chemicalId, quantity: parseQuantityFromForm(raw) });
  }
  return rows;
}
