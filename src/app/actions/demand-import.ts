"use server";

import { createClient } from "@/lib/supabase/server";
import { markDemandExcelImportCompleted } from "@/lib/demand/excel-import-metadata";
import { parseDemandExcelBuffer } from "@/lib/demand/parse-excel";

export type ImportDemandResult =
  | { ok: true; sheetName: string; customersImported: number; chemicalsCount: number }
  | { ok: false; error: string };

const UPSERT_CHUNK = 500;

/**
 * Import demand data from an Excel file matching the template (Master sheet).
 * @param replace - if true, deletes this user's existing customers & chemicals first, then imports.
 */
function resolveFormData(
  a: ImportDemandResult | null | FormData,
  b?: FormData,
): FormData | null {
  if (b instanceof FormData) return b;
  if (a instanceof FormData) return a;
  return null;
}

function trimOrNull(value: string | null): string | null {
  if (value === null || value === undefined) return null;
  const s = String(value).trim();
  return s === "" ? null : s;
}

export async function importDemandExcelAction(
  a: ImportDemandResult | null | FormData,
  b?: FormData,
): Promise<ImportDemandResult> {
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

  const file = formData.get("file");
  if (!file || !(file instanceof File) || file.size === 0) {
    return { ok: false, error: "Choose an Excel file (.xlsx)." };
  }

  const replace = formData.get("replace") === "true";

  let parsed;
  try {
    const buf = await file.arrayBuffer();
    parsed = await parseDemandExcelBuffer(buf);
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "Could not read that Excel file.",
    };
  }

  if (replace) {
    const { error: delCustomers } = await supabase
      .from("customers")
      .delete()
      .eq("user_id", user.id);
    if (delCustomers) {
      return { ok: false, error: delCustomers.message };
    }
    const { error: delChems } = await supabase
      .from("chemicals")
      .delete()
      .eq("user_id", user.id);
    if (delChems) {
      return { ok: false, error: delChems.message };
    }
  }

  let chemicalsCount = 0;
  const nameToId = new Map<string, string>();

  if (parsed.chemicalColumnNames.length > 0) {
    const chemicalRows = parsed.chemicalColumnNames.map((name, i) => ({
      user_id: user.id,
      name,
      sort_order: i,
      updated_at: new Date().toISOString(),
    }));

    const { data: insertedChems, error: chemErr } = await supabase
      .from("chemicals")
      .upsert(chemicalRows, { onConflict: "user_id,name" })
      .select("id,name");

    if (chemErr) {
      return {
        ok: false,
        error:
          chemErr.message ??
          "Failed to save chemicals. Did you run the database migration?",
      };
    }
    if (!insertedChems?.length) {
      return {
        ok: false,
        error: "No chemical rows returned after save. Check Supabase policies and constraints.",
      };
    }
    chemicalsCount = insertedChems.length;
    for (const c of insertedChems) {
      nameToId.set(c.name, c.id);
    }
  }

  // Unique rows per account_name (customers table has a unique constraint per account).
  // Service fields come from the *last* Excel row per account.
  //
  // Chemical quantities must be merged across all Excel rows for the same account:
  // some template rows can contain blank cells while other rows for the same account
  // contain the actual quantities. We keep the last non-blank value per chemical.
  const lastByAccount = new Map<string, (typeof parsed.rows)[0]>();
  const quantitiesByAccount = new Map<string, Record<string, number>>();
  for (const row of parsed.rows) {
    lastByAccount.set(row.account, row);

    const existing = quantitiesByAccount.get(row.account) ?? {};
    for (const [chemName, qty] of Object.entries(row.quantities)) {
      if (qty !== null && qty !== undefined) {
        // Keep last non-null encountered value.
        existing[chemName] = qty;
      }
    }
    quantitiesByAccount.set(row.account, existing);
  }
  const uniqueRows = [...lastByAccount.values()];

  if (uniqueRows.length === 0) {
    await markDemandExcelImportCompleted(supabase);
    return {
      ok: true,
      sheetName: parsed.sheetName,
      customersImported: 0,
      chemicalsCount,
    };
  }

  const now = new Date().toISOString();
  // Preserve Excel text for service columns (trim only; no coercion to enum lists).
  const customerPayload = uniqueRows.map((row) => ({
    user_id: user.id,
    account_name: row.account,
    service_day: trimOrNull(row.serviceDay),
    service_frequency: trimOrNull(row.serviceFrequency),
    service_tech: trimOrNull(row.serviceTech),
    updated_at: now,
  }));

  const { data: savedCustomers, error: custErr } = await supabase
    .from("customers")
    .upsert(customerPayload, { onConflict: "user_id,account_name" })
    .select("id,account_name");

  if (custErr || !savedCustomers?.length) {
    return {
      ok: false,
      error: custErr?.message ?? "Failed to save customers.",
    };
  }

  const accountToId = new Map(savedCustomers.map((c) => [c.account_name, c.id]));

  const ccRows: { customer_id: string; chemical_id: string; quantity: number | null }[] =
    [];
  for (const row of uniqueRows) {
    const customerId = accountToId.get(row.account);
    if (!customerId) continue;

    const mergedQuantities = quantitiesByAccount.get(row.account) ?? {};
    for (const [chemName, qty] of Object.entries(mergedQuantities)) {
      const chemicalId = nameToId.get(chemName);
      if (!chemicalId) continue;

      ccRows.push({
        customer_id: customerId,
        chemical_id: chemicalId,
        quantity: qty,
      });
    }
  }

  for (let i = 0; i < ccRows.length; i += UPSERT_CHUNK) {
    const slice = ccRows.slice(i, i + UPSERT_CHUNK);
    const { error: ccErr } = await supabase.from("customer_chemicals").upsert(slice, {
      onConflict: "customer_id,chemical_id",
    });
    if (ccErr) {
      return { ok: false, error: ccErr.message };
    }
  }

  await markDemandExcelImportCompleted(supabase);

  return {
    ok: true,
    sheetName: parsed.sheetName,
    customersImported: uniqueRows.length,
    chemicalsCount,
  };
}
