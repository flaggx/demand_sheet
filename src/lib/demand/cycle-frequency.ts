/** Matches deprecated RouteViewer cycle / Call In detection. */

export const CYCLE_FREQ_OPTIONS = ["Cycle 1", "Cycle 2", "Cycle 3", "Cycle 4", "Call In"] as const;

export type CycleFreqOption = (typeof CYCLE_FREQ_OPTIONS)[number];

/**
 * True if the cell value belongs to the given cycle option (substring / digit rules).
 */
export function cellMatchesCycleOption(cellValue: unknown, option: string): boolean {
  if (cellValue === null || cellValue === undefined) return false;
  const s = String(cellValue).trim();
  if (!s) return false;
  if (option === "Call In") {
    return s.toLowerCase().includes("call in");
  }
  if (option === "Cycle 1") {
    return /(^|[^\d])1($|[^\d])/.test(s);
  }
  if (option === "Cycle 2") {
    return /(^|[^\d])2($|[^\d])/.test(s);
  }
  if (option === "Cycle 3") {
    return /(^|[^\d])3($|[^\d])/.test(s);
  }
  if (option === "Cycle 4") {
    return /(^|[^\d])4($|[^\d])/.test(s);
  }
  return false;
}
