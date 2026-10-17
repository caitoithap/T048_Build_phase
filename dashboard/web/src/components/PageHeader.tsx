// Đầu trang: vị trí trong menu, công tắc số thật/số giả, và câu hỏi mà trang trả lời làm tiêu đề.
import { ChevronRight, Hourglass } from "lucide-react";
import type { Meta, PageInfo } from "../lib/api";
import { useView } from "../lib/view";
import { Segmented } from "./ui";

function DataSwitch({ meta }: { meta: Meta }) {
  const { demo, update } = useView();
  const value = meta.has_real_files && !demo ? "real" : "mock";
  return (
    <Segmented
      label="Nguồn số liệu"
      value={value}
      onChange={(v) => update((next) => (v === "mock" ? next.set("demo", "true") : next.delete("demo")))}
      options={[
        {
          value: "real",
          label: "Số thật",
          disabled: !meta.has_real_files,
          title: meta.has_real_files ? undefined : "Chưa có file thật nào trong thư mục bảng thật. Xem trang Nguồn dữ liệu.",
        },
        { value: "mock", label: "Số giả" },
      ]}
    />
  );
}

export function PageHeader({ page, meta }: { page: PageInfo; meta: Meta }) {
  const section = meta.sections.find((s) => s.pages.some((p) => p.path === page.path));
  return (
    <header>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-1.5 text-[13px] text-muted">
          {section?.title}
          <ChevronRight aria-hidden className="size-3.5" />
          <span className="font-medium text-ink2">{page.title}</span>
        </p>
        <DataSwitch meta={meta} />
      </div>
      <h1 className="mt-4 max-w-[34em] text-[26px] leading-[1.2] font-semibold tracking-[-0.02em] text-balance sm:text-[32px]">
        {page.question}
      </h1>
      {page.badge.kind === "partial" && (
        <p className="mt-3 flex items-center gap-2 text-[13px] text-ink2">
          <Hourglass aria-hidden className="size-3.5 text-muted" />
          {page.badge.hint}
        </p>
      )}
    </header>
  );
}
