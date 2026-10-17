import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Khi chạy dev, mọi request /api chuyển sang FastAPI (uvicorn api.main:app --port 8000).
// API chạy ở cổng khác thì đặt biến môi trường M22_API_URL, ví dụ http://127.0.0.1:8010.
const api = process.env.M22_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Chunk vega-embed (~830 kB) chỉ tải khi trang có biểu đồ (xem VegaChart.tsx), không nằm trong bundle chính.
  build: { chunkSizeWarningLimit: 900 },
  server: {
    port: 5173,
    proxy: { "/api": api },
  },
});
