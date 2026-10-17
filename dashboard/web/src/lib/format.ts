import type { Cell } from "./api";

const integer = new Intl.NumberFormat("en-US");
const decimal = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });
const ISO = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/;

/** "2026-09-21T14:31:28.26" -> "21/09 14:31". Đọc thẳng từ chuỗi để không lệch múi giờ. */
export function shortTime(iso: string | null): string {
  const m = iso?.match(ISO);
  return m ? `${m[3]}/${m[2]} ${m[4]}:${m[5]}` : "";
}

/** Một ô bảng: số có phân cách nghìn, đúng/sai thành Có/Không, trống thành gạch ngang. */
export function cell(value: Cell): string {
  if (value === null) return "–";
  if (typeof value === "boolean") return value ? "Có" : "Không";
  if (typeof value === "number") return Number.isInteger(value) ? integer.format(value) : decimal.format(value);
  const m = value.match(ISO);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : value;
}
