import { Construction } from "lucide-react";

/** Trang chưa có route ở API. Trong lúc chuyển, bản Streamlit vẫn chạy song song. */
export function NotPortedPage() {
  return (
    <div className="flex flex-col items-start rounded-xl border border-dashed border-line-strong bg-surface px-6 py-10 sm:px-10">
      <Construction aria-hidden className="size-6 text-muted" strokeWidth={1.75} />
      <p className="mt-4 text-[16px] font-semibold">Trang này chưa chuyển sang bản mới</p>
      <p className="mt-1.5 max-w-[42em] text-[14px] leading-relaxed text-ink2">
        Số liệu và biểu đồ của trang vẫn xem được ở bản Streamlit. Từ thư mục gốc của project, chạy{" "}
        <code className="rounded bg-soft px-1 py-px font-mono text-[0.86em] text-ink">streamlit run dashboard/app.py</code>.
      </p>
    </div>
  );
}
