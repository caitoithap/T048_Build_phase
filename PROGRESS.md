# NHẬT KÝ TIẾN ĐỘ – M22 (theo PLAN.md)

Mỗi bước trong `PLAN.md` sau khi làm xong được ghi lại ở đây: đã làm gì, kiểm tra bằng lệnh nào, kết quả ra sao, còn gì dở.

---

## Bước 1 – Đồng bộ cấu hình ✅ (18/10/2026)
- Thêm các hằng số mặc định vào `config.py`: `DEFAULT_MODEL`, `DEFAULT_CONF_THRESHOLD`, `DEFAULT_MIN_BOX_SIZE`, `DEFAULT_MAX_BOX_ASPECT_RATIO`, `TARGET_CLASSES`.
- `cli.py` tự nạp `sample_data_output1/annotations.xml` nếu `output/pre_annotations_cvat.xml` chưa tồn tại.
- Khởi tạo `YOLOCPUDetector`, `QCFilter` và chạy `cli.py` thành công.

## Bước 2 – Bộ test tự động ✅ (18/10/2026)
- Thêm `__contains__` cho dataclass `Tables` (`dashboard/data_layer/store.py`).
- 4 bộ test: `test_qc_rules.py`, `test_data_layer.py`, `test_api_endpoints.py`, `test_cli.py`. Kết quả lúc đó: 15/15 pass.

## Bước 3 – Chuyển 8 trang phân tích sang API ✅ (18/10/2026)
- Đối chiếu 6 file đã có (`top_errors`, `classes`, `annotators`, `cross_annotators`, `cross_reviewers`, `fix_annotator`) với `dashboard/views/`: cách tính số giống bản Streamlit, đã dùng `api/blocks.py`.
- Viết mới `dashboard/api/pages/fix_agent.py` và `dashboard/api/pages/fix_recommendations.py` từ `views/`.
  - `fix_agent`: giữ đủ ghi chú mô phỏng, 5 KPI, phễu, ma trận agent × người duyệt, biểu đồ theo thao tác. Khung "Xem một bản vá" (chọn bản vá, ảnh trước/sau) cần tương tác nên chưa chuyển; thay bằng bảng "Bản vá đã có quyết định" (tối đa 300 dòng), ảnh xem ở trang Chi tiết issue.
  - `fix_recommendations`: bảng khuyến nghị đổi tên cột sang tiếng Việt thay cho `column_config` của Streamlit.
- Đăng ký đủ 9 trang trong `dashboard/api/pages/__init__.py`.
- Thêm vào `tests/test_api_endpoints.py`: test mỗi trang × `demo=false/true` × `dark=false/true` (36 ca, kiểm tra 200 và cấu trúc hàng/khối), test `/api/meta` báo mọi trang `ported`, test trang lạ trả 404.
- Kiểm tra: `.venv/bin/pytest tests/test_api_endpoints.py -v` pass. Cả 9 trang đều vẽ biểu đồ/bảng thật, không trang nào chỉ có thẻ chờ dữ liệu.

## Bước 4 – Đồng bộ frontend ✅ (18/10/2026)
- `web/src/lib/icons.tsx` đã đủ 11 icon cho 11 trang trong `catalog.py` (kiểm tra tự động). Không cần sửa React: `App.tsx` dùng `AnalyticsPage` chung cho mọi trang `ported`, `Blocks.tsx` vẽ đủ các loại khối (`kpis`, `chart`, `table`, `pending`, `notice` gồm tone `simulated`, `empty`) mà các trang mới trả về.
- Kiểm tra (đã sửa lệnh cũ sai đường dẫn import): `cd dashboard && ../.venv/bin/python -c "from api.pages import BUILDERS, PORTED; import catalog; assert len(BUILDERS) == 9; assert set(catalog.PAGES) <= PORTED"`: pass.
- `npm run typecheck`: sạch, không lỗi (sau khi cài Node ở Bước 7).
- Bấm thử tự động bằng Playwright (Chromium headless, cài trong venv riêng ở scratchpad) trên bản production build (`vite preview` + API): 11 trang × sáng/tối × số thật/số giả = 44 lượt. Không có lỗi console, không có request `/api` lỗi, không trang nào hiện "chưa chuyển" hay "Không vẽ được biểu đồ". Số biểu đồ vẽ ra khớp số khối chart API trả về. Trang Chi tiết issue hiện ảnh crop có box. Ở bề rộng 400px (tong-quan, sua-agent, cham-cheo-annotator) không bị tràn ngang.
- Từ ảnh chụp: đặt tên cột tiếng Việt cho bảng "Bản vá đã có quyết định" của `fix_agent` (bảng do em thêm ở Bước 3).
- **Lỗi đã biết, chưa sửa:** ở bề rộng điện thoại, heatmap "Đề xuất của agent × quyết định của người" (và các heatmap có nhãn cột dài) bị chồng nhãn cột, chữ trong ô bị cắt. Nguyên nhân: spec heatmap dùng chung (`ui/charts.py`) không co theo bề rộng; bản Streamlit cũng vậy. Sửa đúng cần làm biểu đồ co giãn trong `VegaChart.tsx`/`charts.py`, ngoài phạm vi PLAN. Bố cục trang vẫn không vỡ.
- Ghi chú: script `.venv/bin/uvicorn` có shebang trỏ tới `/media/trong-hung/New Volume1/...` (venv tạo khi ổ đĩa mount ở đường dẫn cũ), nên chạy `.venv/bin/uvicorn` sẽ lỗi. Dùng `.venv/bin/python -m uvicorn` (cách `run_dashboard.sh` đang dùng), hoặc tạo lại `.venv`.

## Bước 5 – Sửa lỗi tồn đọng ✅ (18/10/2026)
- 5.1: thêm `CVAT_SERVER_URL`, `CVAT_USERNAME`, `CVAT_PASSWORD` vào `config.py` (đọc biến môi trường, mặc định `https://app.cvat.ai` và rỗng). `import src.cvat_uploader` không còn lỗi.
- 5.2: thêm `python-dotenv>=1.0.0` vào `requirements.txt`.
- 5.3: `cli.py --mock-cvat` đổi sang `argparse.BooleanOptionalAction`, nên `--no-mock-cvat` bỏ qua bước giả lập CVAT.
- 5.4: `pyarrow` đưa vào `dashboard/requirements.txt` (Bước 6).
- 5.5: warm-up nằm trong `ExecStartPost` của `deploy/m22-api.service`.
- Thêm test `test_cli_no_mock_cvat`, `test_cvat_uploader_imports` vào `tests/test_cli.py`.
- Kiểm tra: `.venv/bin/pytest tests/ -v` → **55/55 pass**.

## Bước 6 – Tách requirements (kèm `deploy/` cho phương án VPS ở phụ lục) ✅ (18/10/2026)
- `dashboard/requirements.txt`: fastapi, uvicorn[standard], pandas, numpy, altair, Pillow, pyarrow.
- `deploy/m22-api.service`, `deploy/nginx-m22.conf` (Basic Auth để sẵn dạng comment; `server_name` là `m22.example.com`, cần đổi), `deploy/deploy.sh`, `deploy/.env.example`.
  - Sửa nhỏ so với PLAN: `deploy.sh` xoá `web.prev` cũ trước khi `cp -a`, nếu không lần deploy thứ hai sẽ chép `web` lồng vào trong `web.prev`.
- `.gitignore` đã bỏ qua `node_modules/`, `dist/`, `.env` và giữ `.env.example`.
- Kiểm tra: tạo venv sạch (trong scratchpad, không có torch hay streamlit), chỉ cài `dashboard/requirements.txt`, chạy `uvicorn api.main:app --port 8001` từ `dashboard/`: `/api/meta`, `/api/data-status` và các trang `?demo=true` đều trả 200.

## Bước 7 – Node.js, Vercel CLI, tài khoản 🟡 (18/10/2026)
- Máy không có sudo không mật khẩu, nên em không cài theo nodesource mà cài **Node.js v22.23.3** (bản LTS chính thức từ nodejs.org, đã kiểm tra SHA256) vào `~/.local/node-v22.23.3-linux-x64`, symlink `~/.local/node`, và thêm `export PATH="$HOME/.local/node/bin:$PATH"` vào `~/.bashrc`. npm 10.9.9.
- `cd dashboard/web && npm ci && npm run typecheck && npm run build`: thành công. Có `dist/index.html`, `dist/assets/index-*.js` (347 kB), chunk vega-embed tách riêng `embed-*.js` (834 kB).
- `npm i -g vercel`: **Vercel CLI 64.5.0**.
- **Còn dở:** `vercel login` cần người dùng đăng nhập bằng trình duyệt (tài khoản GitHub của chủ repo). `vercel whoami` hiện báo "Logged out".

## Bước 8 – Entry Python cho Vercel ✅ (18/10/2026)
- Tạo `api/index.py`, `api/requirements.txt` (không uvicorn, không pyarrow), `.python-version` (`3.12`), đúng nội dung PLAN.
- Máy chỉ có Python 3.10, nên em cài Python 3.12.15 độc lập bằng `uv` vào scratchpad, tạo venv chỉ cài `api/requirements.txt` + pytest + httpx:
  - `runpy.run_path('api/index.py')` → `<class 'fastapi.applications.FastAPI'>`.
  - Import dạng module `api.index` từ gốc repo (trường hợp dễ trùng tên `api` nhất): nạp đúng `dashboard/api`, `/api/meta?demo=true` và `/api/pages/sua-agent?demo=true` trả 200.
  - `pytest tests/test_api_endpoints.py tests/test_data_layer.py` trên 3.12: **45/45 pass** (test CLI/QC cần torch, không chạy trên Vercel).
- Kích thước: site-packages của bộ gói này trên 3.12 ≈ 200 MB khi đã trừ pip/pytest/pygments (pandas 72 MB, numpy 43 + numpy.libs 27 MB, Pillow 8 + pillow.libs 15 MB, altair 10 MB…), cộng ~13 MB dữ liệu ≈ **215 MB, dưới giới hạn 250 MB nhưng ít dư hơn ước tính ~135 MB trong PLAN**. Cần xem số thực ở Bước 10.

## Bước 9 – `vercel.json` và `.vercelignore` 🟡 (18/10/2026)
- Tạo `vercel.json` (JSON hợp lệ) và `.vercelignore` đúng nội dung PLAN; thêm `.vercel` vào `.gitignore`.
- Đã xác nhận `sample_data_output1/annotations.xml` (968 KB) và `images.zip` (12 MB) có trong git và không bị `.vercelignore` bỏ.
- **Còn dở:** `vercel build` (tiêu chí hoàn thành) báo "The specified token is not valid. Use `vercel login`": cần đăng nhập trước.

## Hàng đợi Q1 – Sửa `.vercelignore` ✅ (18/10/2026)
- Xác nhận lỗi bằng `ignore@5` (cài trong scratchpad): bản cũ bỏ mất `dashboard/web/src/App.tsx` (mẫu `src/` khớp ở mọi cấp), nên build trên Vercel sẽ hỏng.
- Viết lại theo Bước 9 mục 2: mọi mục chỉ nằm ở gốc repo có `/` ở đầu. Lệnh kiểm tra ở Q1 → `OK`; kiểm tra thêm `dashboard/app.py` không bị bỏ.

## Hàng đợi Q2 – Test cấu hình Vercel ✅ (18/10/2026)
- File mới `tests/test_vercel_config.py`, 4 test: entry `api/index.py` trả `FastAPI` và `/api/meta`, `/api/pages/tong-quan` (demo) trả 200; nội dung `vercel.json`; `api/requirements.txt` không có torch/ultralytics/opencv/pyarrow/streamlit/uvicorn; `.vercelignore` giữ/bỏ đúng hai danh sách (thêm `dashboard/app.py` vào danh sách giữ).
- Cài `pathspec` 1.1.1 vào `.venv` (`.venv/bin/python -m pip`, vì `.venv/bin/pip` có shebang hỏng như `uvicorn`). PLAN ghi kiểu `gitwildmatch`, nhưng pathspec 1.x đã đánh dấu deprecated (41 cảnh báo), nên dùng `pathspec.GitIgnoreSpec` (cùng cú pháp `.gitignore`).
- Thử phản chứng: tạm thêm `src/` → test fail với `['dashboard/web/src/App.tsx']`; tạm thêm `app.py` → fail với `['dashboard/app.py']`. Đã khôi phục file.
- `.venv/bin/python -m pytest tests/ -q` → **59/59 pass**.

## Hàng đợi Q3 – Ghim phiên bản 🟡 (18/10/2026)
- Q3.1 ✅: `api/requirements.txt` ghim `fastapi==0.144.0`, `pandas==3.0.6`, `numpy==2.5.4`, `altair==6.3.0`, `Pillow==13.0.0` (khớp đúng bộ đang chạy trong venv 3.12). Tạo lại venv 3.12 từ đầu theo file đã ghim: `test_api_endpoints` + `test_data_layer` + `test_vercel_config` → **49/49 pass**.
- Q3.2: chưa làm, chỉ làm nếu ở Q6 function > 230 MB.

## Hàng đợi Q4 – 👤 Người dùng trả lời 🟡 (18/10/2026)
- Trả lời: (1) Bước 12 chọn **a. công khai**, nên Q9 không cần làm gì; (2) repo: người dùng trả lời **private**; (3) **cho phép** commit, push nhánh `deploy/vercel` và mở PR.
- ⚠️ **Lệch thông tin:** GitHub API (`api.github.com/repos/caitoithap/T048_Build_phase`) trả `"visibility": "public"`, và `git ls-remote` chạy được mà không cần đăng nhập. Repo thực tế đang **public**, nên **không được commit CSV thật** ở Bước 14 cho tới khi chuyển repo sang private.
- Còn chờ: `vercel login` (người dùng gõ).
- Vercel CLI vẫn "Logged out". Máy chưa có `gh` (Q7 cần), nên đã cài sẵn **GitHub CLI 2.102.0** vào `~/.local/gh_2.102.0_linux_amd64` (đã kiểm tra SHA256), symlink `~/.local/bin/gh`, thêm `~/.local/bin` vào PATH trong `~/.bashrc`.

## Hàng đợi Q10 – Tài liệu theo Vercel ✅ (18/10/2026)
- `README.md`: thêm mục "6. Deploy to Vercel" (kiến trúc, file cấu hình, cách kiểm tra, dữ liệu thật chỉ `.csv` và commit vào `dashboard/data_real/`); phương án VPS chỉ còn một dòng trỏ tới phụ lục `PLAN.md`; thêm `api/` vào cây thư mục.
- `dashboard/README.md`: thay mục "Triển khai" (VPS) bằng "Triển khai (Vercel)": vì sao có `api/index.py` ở gốc, gói và giới hạn 250 MB, quy tắc `.vercelignore`, dữ liệu thật chỉ `.csv` qua PR.
- `REPORT.md`: dòng chuẩn bị triển khai đổi sang Vercel; 5 bộ test, 59/59 pass.
- Còn chờ URL production và kết quả smoke test (Q8).

## Hàng đợi Q4 – bổ sung (18/10/2026)
- Người dùng xác nhận: dữ liệu theo **public** (repo public), nên Bước 14 chỉ commit dữ liệu giả hoặc đã ẩn danh.
- Vercel CLI đăng nhập: `vercel whoami` → `caitoithap`. GitHub CLI (`gh`) **chưa đăng nhập**, nên chưa push/mở PR được (Q7).

## Hàng đợi Q5 – Link project và `vercel build` ✅ (18/10/2026)
- `vercel link --yes --project m22-dashboard`: tạo project mới (`prj_P1aCsLEF9riCVETwyL1ndDPVSTC6`). CLI tự thêm `.vercel` và `.env*` vào `.gitignore`; dòng `.env*` nằm sau `!.env.example` nên đã sắp lại (giữ `deploy/.env.example`).
- `vercel build` ở máy cần `uv` trong PATH: dùng `uv` 0.13.1 trong venv scratchpad.
- **Lần build đầu lỗi `LAMBDA_SIZE_EXCEEDED` (382,77 MB, giới hạn của builder là 225 MB, không phải 250 MB).** Đọc mã nguồn `@vercel/python` (đi kèm CLI 64.5.0) thì thấy hai nguyên nhân:
  1. Builder tự quét `**` toàn repo (đã loại sẵn `node_modules`, `.venv`, `.vercel`), rồi mới thêm các file khớp `includeFiles` **sau** bước `excludeFiles` (`Object.assign(files, initialFiles)`). Mẫu `dashboard/**` trong PLAN kéo theo `dashboard/web/node_modules` (224 MB).
  2. Ở máy, builder nhắm glibc 2.17, nên wheel numpy/pandas/pillow (cần ≥ 2.27/2.28) bị coi là không tương thích và bị force-bundle. Trên build image của Vercel thì builder đọc glibc thật (`VERCEL_BUILD_IMAGE`), nên đây chỉ là lỗi ở máy.
- Sửa `vercel.json`: `includeFiles` chỉ còn `{sample_data_output1/annotations.xml,sample_data_output1/images.zip}`; `excludeFiles` thêm `_uv/**`, `.env*`, `.pytest_cache/**` và các mục chỉ có ở máy (`src/**`, `tests/**`, `output/**`, `sample_data/**`, `deploy/**`, `*.pt`, `app.py`, `cli.py`, `config.py`, các file `.md` ở gốc), để build ở máy khớp với cloud (trên cloud, `.vercelignore` đã loại lúc upload). Lần build có `.env.local` (chứa `VERCEL_OIDC_TOKEN`) lọt vào gói → đã loại.
- Kết quả: **build OK, gói function 142,96 MB** (thư viện 136,4 MB + dữ liệu 13,3 MB), mọi gói đều bundle sẵn, không phải cài lúc chạy. Có `images.zip`, `annotations.xml`; không có torch, `node_modules`, `views/`. `.vercel/output/static/index.html` có. Runtime `python3.12`.
- Builder đọc phiên bản Python từ `api/.python-version` (thư mục chứa `requirements.txt`), không phải file ở gốc; build tự sinh `api/.python-version` (3.12), `api/pyproject.toml`, `api/uv.lock`. Commit `api/.python-version` cho rõ ràng; `pyproject.toml` + `uv.lock` là sản phẩm sinh ra nên đưa vào `.gitignore`. Thư mục `_uv/` (uv bundle) cũng đưa vào `.gitignore`.
- Thêm test vào `tests/test_vercel_config.py`: `includeFiles` không chứa `dashboard/**`, `excludeFiles` có `.env*`. `pytest tests/` → **59/59 pass**.
- Q3.2 (bỏ thư mục test của pandas/numpy) **không cần** vì gói còn 143 MB.

## Hàng đợi Q6 – `vercel dev` và preview 🟡 (18/10/2026)
- `vercel dev`: trang tĩnh trả 200, nhưng mọi `/api/*` trả 500 do lỗi của chính công cụ: `DEV_BUILDER_RESULT_HAS_MAXDURATION: The result of "builder.build()" must not contain maxDuration` (CLI ghi "likely a bug in the Builder"). `vercel build` và bản cloud chạy được với cùng cấu hình, nên không sửa `vercel.json` để chiều lỗi này.
- `vercel deploy --yes` (không có `--prod`). ⚠️ Vì là **lần deploy đầu của project, Vercel tự gán nó làm production**: **https://m22-dashboard.vercel.app** (deployment `m22-dashboard-fjuuwbkyv-caitoithaps-projects.vercel.app`). Chỉ chứa dữ liệu giả, người dùng chọn công khai. Các lần deploy sau mặc định là preview.
- Build log trên cloud: Python 3.12 từ `api/.python-version`, cài từ uv.lock theo bộ gói đã ghim, không có torch, build 13 s, không có cảnh báo dung lượng.
- Checklist Bước 10.4: build không torch ✅; dung lượng ~143 MB < 225 MB ✅; `/api/meta` 200 (import đúng `dashboard/api`, không trùng tên) ✅; `/api/pages/tong-quan?demo=true` 200 (FastAPI nhận đúng path gốc sau rewrite) ✅; `/api/issues/ISS-00001/crop.jpg` trả `image/jpeg` ✅; F5 `/top-loi` 200 ✅; không có lỗi 503 đáp án ✅.
- Tạo `deploy/smoke_vercel.sh BASE [USER:PASS]` (hỗ trợ `VERCEL_BYPASS` cho preview bị khoá): 26 kiểm tra (index, SPA fallback, meta, data-status, sample.zip, 9 trang × sáng/tối, chi tiết issue, ảnh crop `image/jpeg`, `/docs` không phải Swagger). Trên URL production: **SMOKE OK**, mọi request 0,2–0,7 s (đã ấm). Thử URL sai → mã thoát 1.
- Playwright trên URL production: 11 trang × sáng/tối × thật/giả, không lỗi console hay request; không tràn ngang ở 400px; Chi tiết issue hiện ảnh crop có box.
- Chưa đo được cold start (chưa có cách ép instance mới); sẽ đo sau lần deploy kế tiếp.

## Bước 10–16 – Preview, production, bảo vệ, hiệu năng, dữ liệu thật, smoke test, vận hành ⛔ chưa làm
- Tất cả cần tài khoản Vercel đã đăng nhập (và quyền repo GitHub cho bước 11). Bước 14 (commit CSV thật) cần dữ liệu thật từ pipeline.

## Bước 17 – Tài liệu 🟡 (18/10/2026)
- `README.md`: bỏ đường dẫn Windows, thêm `dashboard/`, `deploy/`, `tests/` vào cây thư mục, thêm mục chạy dashboard FastAPI + React, chạy test và trỏ tới hướng dẫn triển khai.
- `dashboard/README.md`: "Đã chuyển" thành đủ 11 trang (kèm ghi chú về khung xem bản vá), thêm mục "Triển khai" (hiện tóm tắt phương án VPS).
- `REPORT.md`: ngày cập nhật 18/10/2026, thêm mục 4.6 (FastAPI + React, 55 test, chuẩn bị triển khai, sửa lỗi cấu hình), bỏ đường dẫn Windows ở phần thông tin.
- Thêm `run_dashboard.sh` ở thư mục gốc: chạy API và Vite dev server bằng một lệnh.
- **Còn dở:** viết lại mục triển khai trong README/dashboard README theo Vercel, ghi URL production và kết quả smoke test (sau Bước 15). 17.4 (xoá Streamlit) chưa làm: khung xem bản vá của trang `sua-agent` hiện mới có ở bản Streamlit.

---

## Rà soát của agent lập kế hoạch (18/10/2026) – đã thêm hàng đợi Q1–Q10 vào `PLAN.md`
- **Lỗi chặn build:** `.vercelignore` ghi `src/` và `app.py` không có `/` ở đầu, nên khớp ở mọi cấp thư mục. Kiểm tra bằng `ignore@5` (cùng cú pháp với Vercel): `dashboard/web/src/App.tsx` → **IGNORED**, `dashboard/app.py` → IGNORED. Hậu quả: build React trên Vercel lỗi vì thiếu `src/`. Cách sửa và lệnh kiểm tra ở **Q1**; nội dung đúng ở Bước 9.2.
- Xác nhận lại ở venv Python 3.12 riêng (chỉ cài `api/requirements.txt`): `runpy.run_path('api/index.py')` cho app chạy được; `/api/meta?demo=true`, `/api/pages/tong-quan`, `/api/pages/sua-agent`, `/api/data-status`, `/api/sample.zip` đều trả 200.
- Phiên bản đã test trên 3.12: fastapi 0.144.0, pandas 3.0.6, numpy 2.5.4, altair 6.3.0, Pillow 13.0.0. Nên ghim trong `api/requirements.txt` (**Q3**).
- Dung lượng: site-packages ~200 MB, sát giới hạn 250 MB. Thư mục test của pandas/numpy ~63 MB, là phương án dự phòng nếu vượt (**Q3.2**).
- Bước 12 cách b: mẫu `middleware.ts` cũ cần `@vercel/functions` nhưng sẽ không được cài (installCommand chỉ chạy trong `dashboard/web`). Đã thay bằng mẫu không phụ thuộc thư viện.
- Việc cần người dùng (Q4): `! PATH="$HOME/.local/node/bin:$PATH" vercel login` (gọi thẳng `~/.local/node/bin/vercel` sẽ lỗi `env: node: No such file`, vì `node` chưa có trong PATH của phiên); chọn cách bảo vệ truy cập; cho biết repo public hay private; cho phép push/PR.
- **Q4 (một phần) – Đã đăng nhập Vercel (18/10/2026):** `vercel whoami` → `caitoithap` (trùng chủ repo GitHub). Agent làm tiếp được Q5–Q6 (link project, `vercel build`, `vercel dev`, preview). Vẫn **chờ người dùng trả lời** Q4.1 (bảo vệ truy cập), Q4.2 (repo public/private), Q4.3 (cho phép push/PR). Chưa có trả lời thì không làm Q7–Q9 và không chạy `vercel --prod`.
