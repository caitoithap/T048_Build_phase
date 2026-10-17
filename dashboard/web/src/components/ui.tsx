// Thành phần giao diện nhỏ dùng lại giữa các trang.
import {
  CircleAlert,
  FilterX,
  FlaskConical,
  Hourglass,
  Info,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useId, type ReactNode, type RefObject } from "react";
import { ApiError, type Tone } from "../lib/api";
import { useView } from "../lib/view";

/** Chữ có `mã` trong dấu backtick: phần trong backtick hiện như mã. */
export function RichText({ text }: { text: string }) {
  return (
    <>
      {text.split("`").map((part, i) =>
        i % 2 ? (
          <code key={i} className="rounded bg-soft px-1 py-px font-mono text-[0.86em] text-ink">
            {part}
          </code>
        ) : (
          part
        ),
      )}
    </>
  );
}

/**
 * Nhãn có giải thích: gạch chân chấm, rê chuột hoặc focus thì hiện.
 * `align="end"` cho nhãn sát mép phải, để bóng mở về bên trái thay vì tràn ra ngoài trang.
 */
export function Tip({ label, text, align = "start" }: { label: ReactNode; text: string; align?: "start" | "end" }) {
  const id = useId();
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-describedby={id}
        className="cursor-help rounded-sm text-left underline decoration-line-strong decoration-dotted underline-offset-[5px] hover:decoration-muted"
      >
        {label}
      </button>
      <span
        id={id}
        role="tooltip"
        className={`pointer-events-none absolute top-full z-40 mt-2 hidden w-72 max-w-[80vw] rounded-lg border border-line-strong bg-raised px-3 py-2.5 text-[13px] leading-relaxed font-normal text-ink2 shadow-pop group-focus-within:block group-hover:block ${
          align === "end" ? "right-0" : "left-0"
        }`}
      >
        {text}
      </span>
    </span>
  );
}

export function Panel({
  title,
  note,
  aside,
  children,
  className = "",
}: {
  title?: ReactNode;
  note?: string | null;
  aside?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`flex h-full min-w-0 flex-col rounded-xl border border-line bg-surface p-5 ${className}`}>
      {(title || aside) && (
        <header className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            {title && <h2 className="text-[15px] leading-snug font-semibold text-ink">{title}</h2>}
            {note && (
              <p className="mt-1 text-[13px] leading-relaxed text-muted">
                <RichText text={note} />
              </p>
            )}
          </div>
          {aside}
        </header>
      )}
      {children && <div className={title || aside ? "mt-4 min-w-0 flex-1" : "min-w-0 flex-1"}>{children}</div>}
    </section>
  );
}

export function Switch({
  label,
  checked,
  onChange,
  disabled = false,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className="inline-flex items-center gap-2 rounded-md text-[13px] text-ink2 hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
    >
      <span
        className={`relative h-[18px] w-8 shrink-0 rounded-full transition-colors ${checked ? "bg-accent" : "bg-line-strong"}`}
      >
        <span
          className={`absolute top-[3px] left-[3px] size-3 rounded-full bg-white shadow-sm transition-transform ${
            checked ? "translate-x-[14px]" : ""
          }`}
        />
      </span>
      {label}
    </button>
  );
}

/** Nhóm nút chọn một trong vài giá trị. */
export function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string; icon?: LucideIcon; disabled?: boolean; title?: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-lg border border-line bg-soft/60 p-0.5">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            disabled={o.disabled}
            title={o.title}
            onClick={() => onChange(o.value)}
            className={`inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-[13px] transition-colors disabled:cursor-not-allowed disabled:opacity-45 ${
              on ? "bg-surface font-medium text-ink shadow-xs" : "text-ink2 enabled:hover:text-ink"
            }`}
          >
            {o.icon && <o.icon aria-hidden className="size-3.5" strokeWidth={2} />}
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

/** Đóng một lớp nổi khi bấm ra ngoài `box` hoặc nhấn Esc. */
export function useDismiss(box: RefObject<HTMLElement | null>, open: boolean, close: () => void) {
  useEffect(() => {
    if (!open) return;
    const outside = (e: MouseEvent) => box.current && !box.current.contains(e.target as Node) && close();
    const escape = (e: KeyboardEvent) => e.key === "Escape" && close();
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [box, open, close]);
}

const TONES: Record<Tone, { icon: LucideIcon; className: string }> = {
  info: { icon: Info, className: "border-accent/25 bg-accent-soft text-ink" },
  warning: { icon: TriangleAlert, className: "border-mock/35 bg-mock-soft text-ink" },
  simulated: { icon: FlaskConical, className: "border-mock/35 bg-mock-soft text-ink" },
  pending: { icon: Hourglass, className: "border-line bg-surface text-ink2" },
  empty: { icon: FilterX, className: "border-line bg-surface text-ink2" },
};

export function Notice({ tone, message }: { tone: Tone; message: string }) {
  const t = TONES[tone];
  return (
    <div className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-[14px] leading-relaxed ${t.className}`}>
      <t.icon aria-hidden className="mt-0.5 size-4 shrink-0 opacity-75" strokeWidth={2} />
      <p className="min-w-0">
        <RichText text={message} />
      </p>
    </div>
  );
}

/** Không còn dòng nào sau khi lọc: nói rõ và đưa nút xoá lọc. */
export function EmptyState({ message = "Không còn dữ liệu với bộ lọc đang chọn." }: { message?: string }) {
  const { filtered, clearFilters } = useView();
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-line-strong bg-surface px-6 py-14 text-center">
      <FilterX aria-hidden className="size-6 text-muted" strokeWidth={1.75} />
      <p className="mt-3 font-medium text-ink">{message}</p>
      {filtered ? (
        <button
          type="button"
          onClick={clearFilters}
          className="mt-4 h-8 rounded-lg border border-line-strong bg-surface px-3 text-[13px] font-medium hover:bg-soft"
        >
          Xoá lọc
        </button>
      ) : (
        <p className="mt-1 text-[13px] text-muted">Bảng nguồn chưa có dòng nào cho phần này.</p>
      )}
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-soft ${className}`} />;
}

export function PageSkeleton() {
  return (
    <div className="flex flex-col gap-4" aria-busy aria-label="Đang tải">
      <Skeleton className="h-[132px]" />
      <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
        <Skeleton className="h-[380px]" />
        <Skeleton className="h-[380px]" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-[320px]" />
        <Skeleton className="h-[320px]" />
      </div>
    </div>
  );
}

/** Đổi lỗi thành: chuyện gì xảy ra, và cần làm gì. */
function explain(error: unknown): { title: string; message: string; fix?: string } {
  if (error instanceof ApiError) {
    if (error.status === 503)
      return {
        title: "Thiếu bộ đáp án",
        message: error.message,
        fix: "Đặt annotations.xml và images.zip vào sample_data_output1/, rồi tải lại trang.",
      };
    if (error.status === 422)
      return { title: "Bộ lọc trên đường dẫn không hợp lệ", message: error.message, fix: "Bấm Xoá lọc, hoặc mở lại trang từ menu." };
    if (error.status === 404) return { title: "Không tìm thấy", message: error.message };
    if (error.status >= 500 && error.message.startsWith("Máy chủ trả lỗi"))
      return {
        title: "Không kết nối được API",
        message: error.message,
        fix: "Kiểm tra uvicorn đang chạy, và M22_API_URL trỏ đúng cổng của nó.",
      };
    return { title: "API báo lỗi", message: error.message };
  }
  if (error instanceof TypeError)
    return {
      title: "Không kết nối được API",
      message: error.message,
      fix: "Kiểm tra uvicorn đang chạy, rồi tải lại trang.",
    };
  return { title: "Lỗi không rõ", message: error instanceof Error ? error.message : String(error) };
}

export function ErrorState({ error }: { error: unknown }) {
  const { title, message, fix } = explain(error);
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-bad/35 bg-bad/[0.06] px-4 py-3.5">
      <CircleAlert aria-hidden className="mt-0.5 size-4 shrink-0 text-bad" strokeWidth={2} />
      <div className="min-w-0 text-[14px] leading-relaxed">
        <p className="font-medium text-ink">{title}</p>
        <p className="text-ink2">
          <RichText text={message} />
        </p>
        {fix && <p className="mt-1 text-ink2">{fix}</p>}
      </div>
    </div>
  );
}
