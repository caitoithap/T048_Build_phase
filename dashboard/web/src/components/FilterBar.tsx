// Hàng lọc của trang, dính trên cùng khi cuộn (từ khổ tablet; trên điện thoại hàng lọc chiếm quá nửa màn hình
// nên cuộn theo trang). Chỉ hiện ô lọc trang dùng; lựa chọn của ô khác vẫn giữ trên URL.
import { Check } from "lucide-react";
import type { FilterName, Meta, PageInfo } from "../lib/api";
import { useView } from "../lib/view";
import { FilterChip } from "./FilterChip";
import { Switch } from "./ui";

const NAMES: Record<FilterName, string> = { run: "lần chạy", class: "class", size: "cỡ box", annotator: "annotator" };
const DEFAULT_SCOPE = "b1_ctrl";

export function FilterBar({ page, options }: { page: PageInfo; options: Meta["options"] }) {
  const { sp, update, showTables, filtered, clearFilters } = useView();
  const on = (name: FilterName) => page.filters.includes(name);
  const skipped = (Object.keys(NAMES) as FilterName[]).filter((name) => !on(name)).map((name) => NAMES[name]);
  const hideSign = sp.get("hide_sign") === "true";

  const setMany = (key: string, values: string[]) =>
    update((next) => {
      next.delete(key);
      values.forEach((v) => next.append(key, v));
    });

  return (
    <div className="relative z-20 -mx-4 mt-6 border-b sm:sticky sm:top-14 border-line bg-page/90 px-4 py-3 backdrop-blur-md sm:-mx-6 sm:px-6 lg:top-0 lg:-mx-10 lg:px-10">
      <div className="flex flex-wrap items-center gap-2">
        {on("run") && (
          <FilterChip
            label="Lần chạy"
            options={options.scopes}
            values={[sp.get("scope") ?? DEFAULT_SCOPE]}
            active={sp.has("scope")}
            onChange={([v]) => update((next) => (v === DEFAULT_SCOPE ? next.delete("scope") : next.set("scope", v)))}
          />
        )}
        {on("class") && (
          <FilterChip
            label="Class"
            multiple
            options={options.classes.map((c) => ({ code: c, label: c }))}
            values={sp.getAll("class")}
            active={sp.has("class")}
            onChange={(v) => setMany("class", v)}
          />
        )}
        {on("size") && (
          <FilterChip
            label="Cỡ box"
            multiple
            options={options.sizes}
            values={sp.getAll("size")}
            active={sp.has("size")}
            onChange={(v) => setMany("size", v)}
          />
        )}
        {on("annotator") && (
          <FilterChip
            label="Annotator"
            multiple
            options={options.annotators.map((a) => ({ code: a, label: a }))}
            values={sp.getAll("annotator")}
            active={sp.has("annotator")}
            onChange={(v) => setMany("annotator", v)}
          />
        )}
        {on("class") && (
          <button
            type="button"
            aria-pressed={hideSign}
            title="Model huấn luyện trên COCO gần như không có class này, nên nó lấn át các lỗi khác."
            onClick={() => update((next) => (hideSign ? next.delete("hide_sign") : next.set("hide_sign", "true")))}
            className={`inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-[13px] transition-colors ${
              hideSign
                ? "border-accent/45 bg-accent-soft font-medium text-accent-ink"
                : "border-dashed border-line-strong text-ink2 hover:border-muted/60 hover:text-ink"
            }`}
          >
            {hideSign && <Check aria-hidden className="size-3.5" strokeWidth={2.5} />}
            Ẩn traffic sign
          </button>
        )}
        <div className="ml-auto flex items-center gap-4 pl-2">
          {filtered && (
            <button type="button" onClick={clearFilters} className="text-[13px] font-medium text-accent-ink hover:underline">
              Xoá lọc
            </button>
          )}
          <Switch
            label="Bảng số liệu"
            checked={showTables}
            onChange={(v) => update((next) => (v ? next.set("tables", "1") : next.delete("tables")))}
          />
        </div>
      </div>
      {skipped.length > 0 && (
        <p className="mt-2 text-[12px] text-muted">Trang này không lọc theo {skipped.join(", ")}.</p>
      )}
    </div>
  );
}
