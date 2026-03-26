import { CYCLE_FREQ_OPTIONS, cellMatchesCycleOption } from "@/lib/demand/cycle-frequency";

/** Canonical weekday names (edit if your Excel uses different spellings). */
export const SERVICE_DAY_OPTIONS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

export type ServiceDay = (typeof SERVICE_DAY_OPTIONS)[number];

/** Same labels as route cycle filters (Cycle 1–4, Call In). */
export const SERVICE_FREQUENCY_OPTIONS = CYCLE_FREQ_OPTIONS;

export type ServiceFrequency = (typeof SERVICE_FREQUENCY_OPTIONS)[number];

/**
 * Three generic tech slots for the dropdown only. Real technician names are not defined in this app —
 * they live in your sheets/data elsewhere. Import keeps Excel cell text as stored; values that do not
 * match these labels still show in the UI (legacy option) until changed.
 */
export const SERVICE_TECH_OPTIONS = [
  "Technician 1",
  "Technician 2",
  "Technician 3",
] as const;

export type ServiceTech = (typeof SERVICE_TECH_OPTIONS)[number];

const DAY_LIST = SERVICE_DAY_OPTIONS as readonly string[];
const FREQ_LIST = SERVICE_FREQUENCY_OPTIONS as readonly string[];
const TECH_LIST = SERVICE_TECH_OPTIONS as readonly string[];

const DAY_ALIASES: Record<string, ServiceDay> = {
  mon: "Monday",
  monday: "Monday",
  tue: "Tuesday",
  tues: "Tuesday",
  tuesday: "Tuesday",
  wed: "Wednesday",
  weds: "Wednesday",
  wednesday: "Wednesday",
  thu: "Thursday",
  thur: "Thursday",
  thurs: "Thursday",
  thursday: "Thursday",
  fri: "Friday",
  friday: "Friday",
  sat: "Saturday",
  saturday: "Saturday",
  sun: "Sunday",
  sunday: "Sunday",
};

export function parseOptionalServiceEnum(
  raw: FormDataEntryValue | null,
  allowed: readonly string[],
  fieldLabel: string,
): { ok: true; value: string | null } | { ok: false; error: string } {
  const s = typeof raw === "string" ? raw.trim() : "";
  if (s === "") return { ok: true, value: null };
  if (allowed.includes(s)) return { ok: true, value: s };
  return { ok: false, error: `Invalid ${fieldLabel}. Choose a value from the list.` };
}

export function parseServiceDayField(
  raw: FormDataEntryValue | null,
): { ok: true; value: string | null } | { ok: false; error: string } {
  return parseOptionalServiceEnum(raw, DAY_LIST, "service day");
}

export function parseServiceFrequencyField(
  raw: FormDataEntryValue | null,
): { ok: true; value: string | null } | { ok: false; error: string } {
  return parseOptionalServiceEnum(raw, FREQ_LIST, "service frequency");
}

export function parseServiceTechField(
  raw: FormDataEntryValue | null,
): { ok: true; value: string | null } | { ok: false; error: string } {
  return parseOptionalServiceEnum(raw, TECH_LIST, "service tech");
}

export function parseServiceFieldsFromForm(formData: FormData):
  | { ok: true; service_day: string | null; service_frequency: string | null; service_tech: string | null }
  | { ok: false; error: string } {
  const d = parseServiceDayField(formData.get("service_day"));
  if (!d.ok) return d;
  const f = parseServiceFrequencyField(formData.get("service_frequency"));
  if (!f.ok) return f;
  const t = parseServiceTechField(formData.get("service_tech"));
  if (!t.ok) return t;
  return {
    ok: true,
    service_day: d.value,
    service_frequency: f.value,
    service_tech: t.value,
  };
}

/** Map Excel / free text to a stored service day, or null if unrecognized. */
export function coerceServiceDayFromExcel(raw: unknown): string | null {
  if (raw === null || raw === undefined || raw === "") return null;
  const s = String(raw).trim();
  if (!s) return null;
  if (DAY_LIST.includes(s)) return s;
  const lower = s.toLowerCase();
  const alias = DAY_ALIASES[lower];
  if (alias) return alias;
  const canon = SERVICE_DAY_OPTIONS.find((d) => d.toLowerCase() === lower);
  return canon ?? null;
}

/** Map Excel cell to Cycle 1–4 / Call In using the same rules as the demand sheet filters. */
export function coerceServiceFrequencyFromExcel(raw: unknown): string | null {
  if (raw === null || raw === undefined || raw === "") return null;
  for (const opt of SERVICE_FREQUENCY_OPTIONS) {
    if (cellMatchesCycleOption(raw, opt)) return opt;
  }
  const s = String(raw).trim();
  if (!s) return null;
  const found = SERVICE_FREQUENCY_OPTIONS.find((o) => o.toLowerCase() === s.toLowerCase());
  return found ?? null;
}

/** Match tech name case-insensitively to configured options. */
export function coerceServiceTechFromExcel(raw: unknown): string | null {
  if (raw === null || raw === undefined || raw === "") return null;
  const s = String(raw).trim();
  if (!s) return null;
  const found = SERVICE_TECH_OPTIONS.find((t) => t.toLowerCase() === s.toLowerCase());
  return found ?? null;
}

export function isAllowedServiceDay(value: string | null | undefined): boolean {
  return value == null || value === "" || DAY_LIST.includes(value);
}

export function isAllowedServiceFrequency(value: string | null | undefined): boolean {
  return value == null || value === "" || FREQ_LIST.includes(value);
}

export function isAllowedServiceTech(value: string | null | undefined): boolean {
  return value == null || value === "" || TECH_LIST.includes(value);
}
