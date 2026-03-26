/** First columns in the Excel template (metadata); remaining columns are chemical quantities. */
export const DEMAND_METADATA_COLUMNS = [
  "Account",
  "Service Day",
  "Service Frequency",
  "Service Tech",
] as const;

export type DemandMetadataColumn = (typeof DEMAND_METADATA_COLUMNS)[number];

/** Prefer this sheet name; otherwise first sheet is used. */
export const DEMAND_EXCEL_MAIN_SHEET = "Master";

/** Set on the auth user in `user_metadata` after a successful Excel import (one-time setup). */
export const DEMAND_EXCEL_IMPORT_COMPLETED_KEY = "demand_excel_import_completed";
