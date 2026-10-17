// Icon của từng trang. catalog.py đặt tên theo bộ Material (bản Streamlit dùng); ở đây đổi sang lucide,
// vẽ bằng SVG nên không phải tải font icon từ ngoài. Thêm trang mới thì thêm một dòng.
import {
  ArrowLeftRight,
  Bot,
  ChartBar,
  Circle,
  Database,
  FlaskConical,
  LayoutDashboard,
  MessageSquareText,
  ScanSearch,
  Shapes,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";

const PAGE_ICONS: Record<string, LucideIcon> = {
  space_dashboard: LayoutDashboard,
  leaderboard: ChartBar,
  category: Shapes,
  group: Users,
  compare_arrows: ArrowLeftRight,
  rate_review: MessageSquareText,
  build: Wrench,
  smart_toy: Bot,
  science: FlaskConical,
  pageview: ScanSearch,
  database: Database,
};

export function PageIcon({ name, className = "size-4" }: { name: string; className?: string }) {
  const Icon = PAGE_ICONS[name] ?? Circle;
  return <Icon aria-hidden className={`shrink-0 ${className}`} strokeWidth={1.75} />;
}
