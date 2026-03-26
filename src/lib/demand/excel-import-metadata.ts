import type { SupabaseClient } from "@supabase/supabase-js";
import { DEMAND_EXCEL_IMPORT_COMPLETED_KEY } from "./constants";

export function isDemandExcelImportCompleted(user: {
  user_metadata?: Record<string, unknown>;
} | null): boolean {
  if (!user?.user_metadata) return false;
  const v = user.user_metadata[DEMAND_EXCEL_IMPORT_COMPLETED_KEY];
  return v === true || v === "true";
}

/** Call after a successful import; failures are logged only (data is already saved). */
export async function markDemandExcelImportCompleted(
  supabase: SupabaseClient,
): Promise<void> {
  const { error } = await supabase.auth.updateUser({
    data: { [DEMAND_EXCEL_IMPORT_COMPLETED_KEY]: true },
  });
  if (error) {
    console.error("markDemandExcelImportCompleted:", error.message);
  }
}
