// Trang phân tích chung: lấy danh sách hàng khối từ /api/pages/<path> rồi vẽ.
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Rows } from "../components/Blocks";
import { ErrorState, PageSkeleton } from "../components/ui";
import { apiGet, type PageData, type PageInfo } from "../lib/api";
import { useTheme } from "../lib/theme";
import { apiParams, useView } from "../lib/view";

export function AnalyticsPage({ page }: { page: PageInfo }) {
  const { sp } = useView();
  const { dark } = useTheme();
  const params = apiParams(sp, { dark: dark ? "true" : undefined });
  const query = useQuery({
    queryKey: ["page", page.path, params.toString()],
    queryFn: () => apiGet<PageData>(`/pages/${page.path}`, params),
    placeholderData: keepPreviousData,
  });

  if (query.isPending) return <PageSkeleton />;
  if (query.isError) return <ErrorState error={query.error} />;
  return (
    <div aria-busy={query.isPlaceholderData} className={`transition-opacity duration-200 ${query.isPlaceholderData ? "opacity-55" : ""}`}>
      <Rows rows={query.data.rows} />
    </div>
  );
}
