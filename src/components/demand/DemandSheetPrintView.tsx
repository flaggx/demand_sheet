"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  CYCLE_FREQ_OPTIONS,
  cellMatchesCycleOption,
} from "@/lib/demand/cycle-frequency";

import "./demand-sheet-print.css";

export type DemandSheetRow = {
  id: string;
  account_name: string;
  service_day: string | null;
  service_frequency: string | null;
  service_tech: string | null;
  quantities: Record<string, number | null>;
};

export type DemandSheetPrintPayload = {
  chemicals: { id: string; name: string; sort_order: number }[];
  rows: DemandSheetRow[];
  generatedAt: string;
};

function uniqSorted(values: (string | null | undefined)[]): string[] {
  const s = new Set<string>();
  for (const v of values) {
    if (v != null && String(v).trim() !== "") s.add(String(v).trim());
  }
  return [...s].sort((a, b) => a.localeCompare(b));
}

function formatQty(q: number | null | undefined): string {
  if (q === null || q === undefined) return "";
  if (typeof q === "number" && Number.isFinite(q)) {
    return Number.isInteger(q) ? String(q) : String(q);
  }
  return "";
}

function cycleFilterActive(selected: Set<string>): boolean {
  return selected.size > 0 && selected.size < CYCLE_FREQ_OPTIONS.length;
}

export function DemandSheetPrintView({
  chemicals,
  rows,
  generatedAt,
}: DemandSheetPrintPayload) {
  const [serviceDay, setServiceDay] = useState("All");
  const [serviceTech, setServiceTech] = useState("All");
  const [cycleSet, setCycleSet] = useState(() => new Set<string>());

  const dayOptions = useMemo(() => {
    return ["All", ...uniqSorted(rows.map((r) => r.service_day))];
  }, [rows]);

  const techOptions = useMemo(() => {
    return ["All", ...uniqSorted(rows.map((r) => r.service_tech))];
  }, [rows]);

  const filteredRows = useMemo(() => {
    const cycleActive = cycleFilterActive(cycleSet);
    return rows.filter((row) => {
      if (serviceDay !== "All" && row.service_day !== serviceDay) return false;
      if (serviceTech !== "All" && row.service_tech !== serviceTech) return false;
      if (cycleActive) {
        const ok = [...cycleSet].some((opt) =>
          cellMatchesCycleOption(row.service_frequency, opt),
        );
        if (!ok) return false;
      }
      return true;
    });
  }, [rows, serviceDay, serviceTech, cycleSet]);

  /** Chemical columns: only show chemicals that have at least one quantity in the current filter. */
  const visibleChemicals = useMemo(() => {
    return chemicals.filter((c) =>
      filteredRows.some((r) => {
        const q = r.quantities[c.id];
        return q !== null && q !== undefined;
      }),
    );
  }, [chemicals, filteredRows]);

  const chemicalTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const c of visibleChemicals) {
      let sum = 0;
      for (const row of filteredRows) {
        const q = row.quantities[c.id];
        if (q !== null && q !== undefined && Number.isFinite(q)) sum += q;
      }
      totals[c.name] = sum;
    }
    return totals;
  }, [visibleChemicals, filteredRows]);

  const { filterHeaderDay, filterHeaderTech, filterHeaderCycle } = useMemo(() => {
    const daysF = uniqSorted(filteredRows.map((r) => r.service_day));
    const techsF = uniqSorted(filteredRows.map((r) => r.service_tech));
    const dayLabel =
      serviceDay !== "All" ? serviceDay : daysF.length === 1 ? daysF[0]! : "All Days";
    const techLabel =
      serviceTech !== "All" ? serviceTech : techsF.length === 1 ? techsF[0]! : "All Techs";
    const cyc = cycleFilterActive(cycleSet)
      ? [...cycleSet].sort().join(", ")
      : "All Frequencies";
    return {
      filterHeaderDay: dayLabel,
      filterHeaderTech: techLabel,
      filterHeaderCycle: cyc,
    };
  }, [filteredRows, serviceDay, serviceTech, cycleSet]);

  function toggleCycle(opt: string) {
    setCycleSet((prev) => {
      const next = new Set(prev);
      if (next.has(opt)) next.delete(opt);
      else next.add(opt);
      return next;
    });
  }

  function selectAllCycles() {
    setCycleSet(new Set([...CYCLE_FREQ_OPTIONS]));
  }

  return (
    <div className="demand-sheet-print-root min-h-screen">
      <div className="sheet-toolbar no-print">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-3 px-4 py-2">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/dashboard/demand"
              className="rounded border border-neutral-500 px-3 py-1.5 text-sm text-neutral-200 hover:bg-neutral-700"
            >
              ← Demand data
            </Link>
            <button
              type="button"
              onClick={() => window.print()}
              className="rounded bg-sky-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-sky-500"
            >
              Print
            </button>
          </div>
          <p className="text-xs text-neutral-400">
            Landscape and grayscale in the print dialog (Ctrl+P)
          </p>
        </div>
      </div>

      <div className="sheet-paper mx-auto max-w-[1400px]">
        <div className="sheet-hint no-print">
          <strong>Print:</strong> Click Print, then in the dialog choose{" "}
          <strong>Landscape</strong> if your browser does not follow the page default. Use grayscale /
          black ink for monochrome output.
        </div>

        <header className="sheet-header">
          <h1>Route Demand Sheet</h1>
          <div className="sheet-header-meta">
            Generated: {generatedAt}
            <br />
            Total records: {filteredRows.length}
          </div>
        </header>

        <div className="sheet-filters">
          <strong>Filters applied:</strong> Service Day: {filterHeaderDay} | Service Tech:{" "}
          {filterHeaderTech} | Service frequency: {filterHeaderCycle}
        </div>

        <div className="no-print space-y-3 rounded border border-neutral-600 bg-neutral-900/90 p-4 text-sm text-neutral-200">
          <div className="flex flex-wrap gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-neutral-500">Service day</span>
              <select
                value={serviceDay}
                onChange={(e) => setServiceDay(e.target.value)}
                className="rounded border border-neutral-600 bg-neutral-950 px-2 py-1.5 text-neutral-100"
              >
                {dayOptions.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-neutral-500">Service tech</span>
              <select
                value={serviceTech}
                onChange={(e) => setServiceTech(e.target.value)}
                className="rounded border border-neutral-600 bg-neutral-950 px-2 py-1.5 text-neutral-100"
              >
                {techOptions.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="text-xs text-neutral-500">Service frequency (cycle)</span>
              <button
                type="button"
                onClick={selectAllCycles}
                className="text-xs text-sky-400 hover:underline"
              >
                Select all (no filter)
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {CYCLE_FREQ_OPTIONS.map((opt) => {
                const selected = cycleSet.has(opt);
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => toggleCycle(opt)}
                    aria-pressed={selected}
                    className={[
                      "rounded border px-3 py-1.5 text-xs transition",
                      selected
                        ? "border-sky-500 bg-sky-600 text-white"
                        : "border-neutral-700 bg-neutral-950 text-neutral-200 hover:bg-neutral-900",
                    ].join(" ")}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-neutral-500">
              Matches the desktop viewer (cycles 1–4 and Call In). With none or all boxes checked,
              every row is shown; check a subset to filter by frequency.
            </p>
          </div>
        </div>

        {rows.length === 0 ? (
          <p className="mt-6 text-neutral-600">No demand data yet. Import Excel or add customers.</p>
        ) : filteredRows.length === 0 ? (
          <p className="mt-6 text-neutral-600">No rows match the current filters.</p>
        ) : (
          <div className="sheet-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Service Day</th>
                  <th>Service Frequency</th>
                  <th>Service Tech</th>
                  {visibleChemicals.map((c) => (
                    <th key={c.id}>{c.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.account_name}</td>
                    <td>{row.service_day ?? ""}</td>
                    <td>{row.service_frequency ?? ""}</td>
                    <td>{row.service_tech ?? ""}</td>
                    {visibleChemicals.map((c) => (
                      <td key={c.id}>{formatQty(row.quantities[c.id])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {visibleChemicals.length > 0 && filteredRows.length > 0 && (
          <div className="sheet-summary">
            <strong>Chemical pick summary:</strong>
            <br />
            {visibleChemicals.map((c) => (
              <span key={c.id}>
                {c.name}: {chemicalTotals[c.name] ?? 0}
                <br />
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
