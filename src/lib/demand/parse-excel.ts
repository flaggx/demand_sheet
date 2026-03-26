import ExcelJS from "exceljs";
import { DEMAND_EXCEL_MAIN_SHEET, DEMAND_METADATA_COLUMNS } from "./constants";

export type ParsedDemandRow = {
  account: string;
  serviceDay: string | null;
  serviceFrequency: string | null;
  serviceTech: string | null;
  /** Chemical column header -> quantity (null = empty cell) */
  quantities: Record<string, number | null>;
};

export type ParsedDemandSheet = {
  sheetName: string;
  chemicalColumnNames: string[];
  rows: ParsedDemandRow[];
};

function cellToPrimitive(cell: ExcelJS.Cell): string | number | null {
  const v = cell.value;
  if (v === null || v === undefined) return null;
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  if (v instanceof Date) return v.toISOString();
  if (typeof v === "object") {
    const o = v as { result?: unknown; richText?: { text: string }[] };
    if ("result" in o && o.result !== undefined) {
      const r = o.result;
      if (typeof r === "number" && Number.isFinite(r)) return r;
      if (typeof r === "string") return r;
      if (r instanceof Date) return r.toISOString();
    }
    if (Array.isArray(o.richText)) {
      return o.richText.map((t) => t.text).join("");
    }
  }
  return String(v);
}

function buildMatrix(worksheet: ExcelJS.Worksheet): (string | number | null)[][] {
  let maxRow = 0;
  let maxCol = 0;
  worksheet.eachRow((row, rowNumber) => {
    maxRow = Math.max(maxRow, rowNumber);
    row.eachCell({ includeEmpty: true }, (_cell, colNumber) => {
      maxCol = Math.max(maxCol, colNumber);
    });
  });
  if (maxRow === 0) {
    return [];
  }
  if (maxCol === 0) {
    const first = worksheet.getRow(1);
    maxCol = Math.max(first.cellCount, 1);
  }

  const matrix: (string | number | null)[][] = [];
  for (let r = 1; r <= maxRow; r++) {
    const row = worksheet.getRow(r);
    const line: (string | number | null)[] = [];
    for (let c = 1; c <= maxCol; c++) {
      line.push(cellToPrimitive(row.getCell(c)));
    }
    matrix.push(line);
  }
  return matrix;
}

function cellToQuantity(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" && !Number.isNaN(value)) return value;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/**
 * Parse demand Excel: "Master" sheet (or first sheet), first row = headers.
 * Uses exceljs (not the `xlsx` package) to avoid known SheetJS npm audit issues.
 */
export async function parseDemandExcelBuffer(buffer: ArrayBuffer): Promise<ParsedDemandSheet> {
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(buffer);

  const worksheet =
    workbook.getWorksheet(DEMAND_EXCEL_MAIN_SHEET) ?? workbook.worksheets[0];

  if (!worksheet) {
    throw new Error("Workbook has no sheets");
  }

  const sheetName = worksheet.name;
  const matrix = buildMatrix(worksheet);

  if (!matrix.length) {
    throw new Error("Sheet is empty");
  }

  const headerRow = matrix[0].map((h) => String(h ?? "").trim());
  const missing = DEMAND_METADATA_COLUMNS.filter((name) => !headerRow.includes(name));
  if (missing.length) {
    throw new Error(
      `Missing required columns: ${missing.join(", ")}. Found: ${headerRow.join(" | ")}`,
    );
  }

  const metaSet = new Set<string>(DEMAND_METADATA_COLUMNS);
  const chemicalColumnNames = headerRow.filter((h) => !metaSet.has(h));

  const rows: ParsedDemandRow[] = [];
  for (let r = 1; r < matrix.length; r++) {
    const line = matrix[r];
    if (!line || line.every((c) => c === null || c === undefined || c === "")) {
      continue;
    }
    const get = (name: string) => {
      const idx = headerRow.indexOf(name);
      if (idx < 0) return null;
      const v = line[idx];
      if (v === null || v === undefined || v === "") return null;
      return String(v).trim();
    };

    const account = get("Account");
    if (!account) continue;

    const quantities: Record<string, number | null> = {};
    for (const chem of chemicalColumnNames) {
      const idx = headerRow.indexOf(chem);
      if (idx < 0) continue;
      quantities[chem] = cellToQuantity(line[idx]);
    }

    rows.push({
      account,
      serviceDay: get("Service Day"),
      serviceFrequency: get("Service Frequency"),
      serviceTech: get("Service Tech"),
      quantities,
    });
  }

  return { sheetName, chemicalColumnNames, rows };
}
