// Vẽ spec Vega-Lite do backend dựng (dashboard/ui/charts.py). Thư viện Vega nặng nên chỉ tải khi cần vẽ.
import { useEffect, useRef, useState } from "react";
import type { VisualizationSpec } from "vega-embed";

export function VegaChart({ spec }: { spec: VisualizationSpec }) {
  const box = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    let finalize: (() => void) | undefined;
    let cancelled = false;
    import("vega-embed")
      .then(({ default: embed }) =>
        // vega-embed có thể ghi vào spec; vẽ trên bản sao để giữ nguyên dữ liệu trong cache.
        // Tooltip "custom" lấy màu từ token của trang (index.css), nên tự theo chế độ sáng/tối.
        embed(el, structuredClone(spec), { actions: false, renderer: "svg", tooltip: { theme: "custom" } }),
      )
      .then((result) => {
        if (cancelled) result.finalize();
        else finalize = result.finalize;
        setFailed(null);
      })
      .catch((error: unknown) => !cancelled && setFailed(error instanceof Error ? error.message : String(error)));
    return () => {
      cancelled = true;
      finalize?.();
    };
  }, [spec]);

  return (
    <>
      <div ref={box} className="w-full min-w-0" />
      {failed && <p className="text-[13px] text-bad">Không vẽ được biểu đồ: {failed}</p>}
    </>
  );
}
