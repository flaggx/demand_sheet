"use client";

export type ChemicalOption = {
  id: string;
  name: string;
};

type Props = {
  chemicals: ChemicalOption[];
  /** Present for chemicals this customer uses; value is quantity (null = blank). */
  initialSelections?: Record<string, number | null>;
};

/**
 * Checkboxes name="chemical_use" value=chemical id; quantities name={`qty_${id}`}.
 */
export function CustomerChemicalsEditor({ chemicals, initialSelections = {} }: Props) {
  if (chemicals.length === 0) {
    return (
      <p className="text-sm text-amber-400/90">
        Add at least one chemical to your catalog before assigning usage.
      </p>
    );
  }

  return (
    <div className="max-h-64 space-y-2 overflow-y-auto rounded border border-neutral-800 bg-neutral-950/80 p-3">
      <p className="text-xs font-medium text-neutral-500">Chemicals in use</p>
      <ul className="space-y-2">
        {chemicals.map((c) => {
          const used = c.id in initialSelections;
          const qty = initialSelections[c.id];
          return (
            <li
              key={c.id}
              className="flex flex-wrap items-center gap-2 text-sm text-neutral-300"
            >
              <label className="flex min-w-0 flex-1 cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  name="chemical_use"
                  value={c.id}
                  defaultChecked={used}
                  className="rounded border-neutral-600"
                />
                <span className="truncate" title={c.name}>
                  {c.name}
                </span>
              </label>
              <input
                type="number"
                name={`qty_${c.id}`}
                step="any"
                placeholder="Qty"
                defaultValue={qty === undefined || qty === null ? "" : String(qty)}
                className="w-24 shrink-0 rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs text-neutral-200"
              />
            </li>
          );
        })}
      </ul>
    </div>
  );
}
