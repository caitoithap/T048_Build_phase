// Chip lọc: bấm mở danh sách, chọn một hoặc nhiều giá trị. Phím mũi tên đi giữa các lựa chọn, Esc đóng.
import { Check, ChevronDown } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { Option } from "../lib/api";
import { useDismiss } from "./ui";

export function FilterChip({
  label,
  options,
  values,
  onChange,
  multiple = false,
  active,
  allLabel = "Tất cả",
}: {
  label: string;
  options: Option[];
  values: string[];
  onChange: (values: string[]) => void;
  multiple?: boolean;
  /** Chip đang lọc khác mặc định thì đổi màu, để thấy ngay trang đang bị lọc ở đâu. */
  active: boolean;
  allLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const close = useCallback(() => setOpen(false), []);
  useDismiss(box, open, close);

  useEffect(() => {
    if (!open) return;
    const items = list.current?.querySelectorAll<HTMLButtonElement>("[role=option]");
    const chosen = list.current?.querySelector<HTMLButtonElement>("[aria-selected=true]");
    (chosen ?? items?.[0])?.focus();
  }, [open]);

  const chosen = options.filter((o) => values.includes(o.code));
  const summary =
    chosen.length === 0 ? allLabel : chosen.length <= 2 ? chosen.map((o) => o.label).join(", ") : `${chosen.length} mục`;

  const pick = (code: string) => {
    if (!multiple) {
      onChange([code]);
      setOpen(false);
      trigger.current?.focus();
      return;
    }
    onChange(values.includes(code) ? values.filter((v) => v !== code) : [...values, code]);
  };

  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") trigger.current?.focus();
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault();
    e.stopPropagation();
    const items = [...(list.current?.querySelectorAll<HTMLButtonElement>("[role=option]") ?? [])];
    const at = items.indexOf(document.activeElement as HTMLButtonElement);
    items[(at + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length]?.focus();
  };

  return (
    <div ref={box} className="relative" onKeyDown={onKey}>
      <button
        ref={trigger}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`inline-flex h-8 max-w-[18rem] items-center gap-1.5 rounded-full border pr-2 pl-3 text-[13px] transition-colors ${
          active
            ? "border-accent/45 bg-accent-soft text-accent-ink"
            : "border-line-strong bg-surface text-ink hover:border-muted/60"
        }`}
      >
        <span className={active ? "opacity-80" : "text-muted"}>{label}</span>
        <span className="truncate font-medium">{summary}</span>
        <ChevronDown aria-hidden className={`size-3.5 shrink-0 opacity-60 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute top-full left-0 z-40 mt-1.5 w-max min-w-56 max-w-[min(20rem,85vw)] rounded-xl border border-line-strong bg-raised p-1 shadow-pop">
          <div ref={list} role="listbox" aria-label={label} aria-multiselectable={multiple} className="max-h-72 overflow-auto">
            {options.map((o) => {
              const on = values.includes(o.code);
              return (
                <button
                  key={o.code}
                  type="button"
                  role="option"
                  aria-selected={on}
                  onClick={() => pick(o.code)}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-[13px] text-ink outline-none hover:bg-soft focus-visible:bg-soft focus-visible:outline-none"
                >
                  <span
                    className={`flex size-4 shrink-0 items-center justify-center ${
                      multiple ? `rounded border ${on ? "border-accent bg-accent text-white" : "border-line-strong"}` : "text-accent"
                    }`}
                  >
                    {on && <Check aria-hidden className="size-3" strokeWidth={3} />}
                  </span>
                  {o.label}
                </button>
              );
            })}
          </div>
          {multiple && values.length > 0 && (
            <button
              type="button"
              onClick={() => onChange([])}
              className="mt-1 w-full rounded-lg border-t border-line px-2.5 py-2 text-left text-[13px] font-medium text-accent-ink hover:bg-soft"
            >
              Bỏ chọn, xem tất cả
            </button>
          )}
        </div>
      )}
    </div>
  );
}
