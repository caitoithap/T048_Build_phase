# KẾ HOẠCH CẢI THIỆN & TRIỂN KHAI HỆ THỐNG M22 LÊN VERCEL (BUILD PHASE)

Dự án: **CVAT Issue Analytics Dashboard & AI Reviewer Agent (M22)**  
Nhóm thực hiện: **T048**  
Repo: `https://github.com/caitoithap/T048_Build_phase`

---

## 🎯 Mục tiêu triển khai

Đưa **Dashboard M22 bản FastAPI + React** lên **Vercel** để cả nhóm và giảng viên mở bằng trình duyệt qua HTTPS. Mỗi lần push lên `main` thì Vercel tự build lại; mỗi Pull Request có một link preview riêng.

**Phạm vi:**

| Thành phần | Lên Vercel? | Chạy dưới dạng |
| :--- | :---: | :--- |
| `dashboard/web` (React + Vite) | ✅ | File tĩnh trên CDN của Vercel (build bằng `vite build`) |
| `dashboard/api` (FastAPI) | ✅ | **Một Vercel Python Function** (`api/index.py`) bọc app FastAPI |
| `sample_data_output1/` (đáp án + `images.zip`) | ✅ | Đóng gói kèm function (chỉ đọc) |
| `dashboard/app.py`, `app.py` (Streamlit) | ❌ | Vercel không chạy được Streamlit (cần server WebSocket chạy liên tục) |
| `cli.py` + `src/` (YOLO, torch) | ❌ | Quá nặng cho serverless (torch vài GB, giới hạn function là 250 MB). Chạy trên máy cá nhân rồi nộp CSV (Bước 14) |

**Kiến trúc đích:**

```
Trình duyệt ──HTTPS──▶ Vercel (một project, một domain *.vercel.app)
                         ├── /assets/*, /index.html  → CDN (dashboard/web/dist)
                         ├── /api/*                  → rewrite → Python Function api/index.py
                         │                                 └── import FastAPI app ở dashboard/api/main.py
                         │                                       ├── đọc sample_data_output1/ (chế độ giả, ảnh)
                         │                                       └── đọc dashboard/data_real/*.csv (dữ liệu thật, commit vào repo)
                         └── mọi đường dẫn khác      → /index.html (SPA, React Router)
```

Frontend gọi API bằng đường dẫn tương đối `/api/...` (`web/src/lib/api.ts`), còn frontend và function nằm cùng domain, nên **không cần CORS và không phải sửa code frontend hay backend**. Mọi thay đổi chỉ là **thêm file cấu hình**.

**Số đo thực tế trên máy (18/10/2026), làm cơ sở cho các giới hạn của Vercel:**

| Chỉ số | Giá trị | Giới hạn Vercel | Đánh giá |
| :--- | :--- | :--- | :---: |
| Thời gian sinh dữ liệu giả lần đầu | ~2,9 s (cộng thêm thời gian import pandas/altair) | `maxDuration` đặt 60 s | ✅ |
| Response lớn nhất (`/api/issues`, `cham-cheo-annotator`) | ~51 KB | 4,5 MB/response | ✅ |
| `/api/sample.zip` | ~532 KB | 4,5 MB | ✅ |
| Gói Python **đo lại trên Python 3.12** (pandas 72 + numpy 43 + numpy.libs 27 + Pillow 8 + pillow.libs 15 + altair 10 + pydantic/fastapi ~11 + narwhals 6 MB…) | **~200 MB** (ước tính ban đầu ~135 MB là đo trên 3.10, thiếu các thư mục `*.libs`) | 250 MB (sau giải nén) | ⚠️ Sát giới hạn: xem phương án giảm ở Q3 |
| Trong đó thư mục test của pandas/numpy (không dùng khi chạy) | ~63 MB | | Bỏ được nếu cần |
| Dữ liệu `sample_data_output1/` | ~13 MB | (tính chung vào 250 MB) | ✅ |
| **pyarrow** | **154 MB** | đẩy tổng lên ~300 MB | ❌ **Không cài trên Vercel** (chỉ nhận `.csv`) |

---

## 📌 Tổng quan các bước

| Bước | Giai đoạn | Nội dung | Trạng thái |
| :---: | :--- | :--- | :---: |
| **1** | A. Hoàn thiện code | Đồng bộ config, CLI tự dùng annotation dự phòng | ✅ Hoàn thành |
| **2** | A. Hoàn thiện code | Bộ test tự động | ✅ Hoàn thành |
| **3** | A. Hoàn thiện code | Chuyển 8 trang phân tích sang `dashboard/api/pages/` | ✅ Hoàn thành (9/9 trang trong `BUILDERS`) |
| **4** | A. Hoàn thiện code | Đồng bộ frontend với các trang mới | ✅ Hoàn thành (typecheck sạch; bấm thử 44 lượt bằng Playwright không lỗi) |
| **5** | A. Hoàn thiện code | Sửa lỗi tồn đọng | ✅ Hoàn thành (5.1–5.4) |
| **6** | A. Hoàn thiện code | Tách `dashboard/requirements.txt` | ✅ Hoàn thành |
| **7** | B. Chuẩn bị | Cài Node.js, Vercel CLI, tạo tài khoản và liên kết GitHub | 🟡 Vercel đã đăng nhập (`caitoithap`); còn `gh auth login` |
| **8** | C. Cấu hình | Entry Python `api/index.py` + `api/requirements.txt` + `.python-version` | ✅ Hoàn thành (kiểm tra trên Python 3.12: 45/45 test) |
| **9** | C. Cấu hình | `vercel.json` (build, rewrites, function) + `.vercelignore` | ✅ `vercel build` OK, gói 143 MB (đã sửa `includeFiles`, xem PROGRESS Q5) |
| **10** | D. Thử | Chạy `vercel dev` ở máy, rồi tạo preview deployment | 🟡 Deploy OK, smoke 26/26; `vercel dev` lỗi của CLI (maxDuration) |
| **11** | E. Production | Tạo project trên Vercel, deploy production, chọn region và domain | ⏳ Chưa bắt đầu |
| **12** | F. Bảo vệ | Giới hạn người xem (Basic Auth bằng Routing Middleware hoặc Password Protection) | ⏳ Chưa bắt đầu |
| **13** | G. Hiệu năng | Giảm cold start, cache tĩnh, giữ function luôn "ấm" | ⏳ Chưa bắt đầu |
| **14** | H. Dữ liệu | Cắm dữ liệu thật (commit CSV, Vercel tự deploy lại) | ⏳ Chưa bắt đầu |
| **15** | I. Kiểm thử | Smoke test trên URL production | ⏳ Chưa bắt đầu |
| **16** | J. Vận hành | Log, rollback, quy trình PR → preview → production | ⏳ Chưa bắt đầu |
| **17** | K. Tài liệu | Cập nhật README.md, REPORT.md, dashboard/README.md | 🟡 Đã cập nhật một phần; còn URL Vercel + kết quả smoke test |

Nhật ký chi tiết từng bước: xem `PROGRESS.md` và mục nhật ký ở cuối file.

---

## 🔜 HÀNG ĐỢI VIỆC TIẾP THEO (agent làm theo thứ tự)

> Bổ sung ngày 18/10/2026, sau khi rà lại các file Vercel đã tạo. Làm xong mục nào thì ghi vào `PROGRESS.md` (mục **Hàng đợi Q…**) và đổi `[ ]` thành `[x]` ở đây. Mục có nhãn **👤** cần người dùng làm hoặc đồng ý trước; gặp mục đó thì dừng lại hỏi, **không tự làm thay**.

- [x] **Q1 – Sửa `.vercelignore` (lỗi chặn build, làm ngay).**
  File này dùng cú pháp `.gitignore`: **mẫu không có `/` ở đầu thì khớp ở mọi cấp thư mục**. Đã kiểm tra bằng thư viện `ignore@5` (cùng cú pháp): hiện tại `src/` xoá luôn **`dashboard/web/src/`**, nên `npm run build` trên Vercel sẽ lỗi vì không còn mã React. `app.py` cũng xoá luôn `dashboard/app.py`.
  Cách sửa: thêm `/` ở đầu mọi mục chỉ nằm ở gốc repo. Nội dung đúng xem ở **Bước 9, mục 2**.
  Kiểm tra (không cần đăng nhập Vercel):
  ```bash
  export PATH="$HOME/.local/node/bin:$PATH"
  D=$(mktemp -d) && (cd "$D" && npm i -s ignore@5 >/dev/null) && NODE_PATH="$D/node_modules" node -e '
  const ig = require("ignore")().add(require("fs").readFileSync(".vercelignore", "utf8"));
  const keep = ["dashboard/web/src/App.tsx","dashboard/web/index.html","dashboard/web/package-lock.json","dashboard/api/main.py",
    "dashboard/settings.py","dashboard/catalog.py","dashboard/data_real/.gitkeep","sample_data_output1/annotations.xml",
    "sample_data_output1/images.zip","api/index.py","api/requirements.txt","vercel.json",".python-version"];
  const drop = ["src/qc_rules.py","app.py","cli.py","config.py","yolov8n.pt","tests/test_cli.py",".venv/bin/python","deploy/deploy.sh"];
  let bad = 0;
  for (const p of keep) if (ig.ignores(p)) { console.log("SAI – bị bỏ:", p); bad++; }
  for (const p of drop) if (!ig.ignores(p)) { console.log("SAI – còn giữ:", p); bad++; }
  console.log(bad ? `${bad} lỗi` : "OK"); process.exit(bad ? 1 : 0);'
  ```

- [x] **Q2 – Test tự động cho cấu hình Vercel**, tạo file mới `tests/test_vercel_config.py`, để lỗi kiểu Q1 không quay lại:
  1. `runpy.run_path("api/index.py")["app"]` là `FastAPI`; `TestClient` gọi `/api/meta?demo=true` và `/api/pages/tong-quan?demo=true` đều trả 200.
  2. `vercel.json`: parse được JSON; có `functions["api/index.py"]`; `includeFiles` chứa `sample_data_output1/annotations.xml` và `sample_data_output1/images.zip`; `rewrites[0]["source"] == "/api/(.*)"`; `outputDirectory == "dashboard/web/dist"`.
  3. `api/requirements.txt` không chứa `torch`, `ultralytics`, `opencv`, `pyarrow`, `streamlit`, `uvicorn`.
  4. `.vercelignore`: dùng `pathspec` (`pytest.importorskip("pathspec")`, kiểu `gitwildmatch`), kiểm tra hai danh sách `keep`/`drop` như ở Q1. Cài `pathspec` vào `.venv` để chạy được: `.venv/bin/pip install pathspec`.
  5. Tiêu chí: `.venv/bin/pytest tests/ -v` pass hết. Test 4 phải **fail** với `.vercelignore` cũ (thử nhanh bằng cách tạm thêm dòng `src/`).

- [x] **Q3 – Ghim phiên bản và chuẩn bị phương án giảm dung lượng.**
  1. Ghim `api/requirements.txt` theo đúng bộ đã test pass trên Python 3.12, để build trên Vercel không tự lên bản mới làm vỡ code hoặc tăng dung lượng:
     ```
     fastapi==0.144.0
     pandas==3.0.6
     numpy==2.5.4
     altair==6.3.0
     Pillow==13.0.0
     ```
     Chạy lại test trên venv 3.12 (cách làm ở `PROGRESS.md`, Bước 8) sau khi ghim.
  2. **Chỉ làm nếu** ở Q6 thấy function > 230 MB hoặc Vercel báo vượt 250 MB: thêm vào `excludeFiles` của `vercel.json` các mẫu `**/pandas/tests/**`, `**/numpy/**/tests/**` (tiết kiệm ~63 MB). Sau đó xác minh lại kích thước function **và** gọi đủ 9 trang, vì đây là giả định chưa kiểm chứng rằng `excludeFiles` áp dụng cả cho gói đã cài.

- [x] **Q4 – 👤 Người dùng đăng nhập Vercel và trả lời 3 câu hỏi.** Agent nhắc người dùng gõ trong Claude Code:
  ```
  ! PATH="$HOME/.local/node/bin:$PATH" vercel login
  ```
  Sau đó hỏi người dùng (một lần, gộp chung):
  1. Bảo vệ truy cập ở Bước 12: **a** công khai / **b** Basic Auth (khuyến nghị, miễn phí) / **c** Password Protection (Pro, trả phí)? Nếu chọn b thì cần tên đăng nhập và mật khẩu, đặt qua `vercel env add`, **không ghi vào repo**.
  2. Repo `caitoithap/T048_Build_phase` đang public hay private? (quyết định có được commit CSV thật ở Bước 14 không)
  3. Có cho phép agent `git push` lên nhánh mới và mở PR không? (Q7)

- [x] **Q5 – Liên kết project và `vercel build` ở máy** (sau Q1–Q4):
  ```bash
  export PATH="$HOME/.local/node/bin:$PATH"
  vercel link --yes --project m22-dashboard
  vercel pull --yes --environment=preview
  vercel build
  du -sh .vercel/output/functions/api/index.func
  ls .vercel/output/static/index.html
  ```
  Ghi vào `PROGRESS.md`: kích thước function, phiên bản Python Vercel dùng, và log cài gói có lấy đúng `api/requirements.txt` không (không được có `torch`).

- [ ] **Q6 – Bước 10: `vercel dev` rồi preview.** Chạy đủ checklist ở Bước 10.4. Preview mặc định được Vercel Authentication bảo vệ nên deploy được ngay. **Không chạy `vercel --prod`** cho tới khi người dùng đồng ý (Q8).
  Viết script kiểm tra dùng lại được: tạo `deploy/smoke_vercel.sh` nhận `BASE` và tuỳ chọn `USER:PASS`, nội dung lấy từ Bước 15 và thêm kiểm tra ảnh crop: lấy một `issue_id` từ `/api/issues?demo=true`, gọi `/api/issues/<id>/crop.jpg?demo=true`, phải nhận `content-type: image/jpeg`. Script trả mã lỗi ≠ 0 nếu có request nào không phải 200. Với preview đang bị bảo vệ, dùng `vercel curl` hoặc bypass token (Settings → Deployment Protection → Protection Bypass for Automation) cho script.

- [ ] **Q7 – 👤 Commit và mở PR** (cần đồng ý ở Q4.3). Hiện có rất nhiều thay đổi chưa commit. Chia commit theo bước, đúng kiểu message tiếng Việt không dấu như lịch sử repo (`feat: ...`, `test: ...`):
  1. `feat: chuyen 8 trang phan tich sang FastAPI (buoc 3)`: `dashboard/api/pages/*`, `tests/test_api_endpoints.py`
  2. `fix: bo sung cau hinh CVAT, python-dotenv, co --no-mock-cvat (buoc 5)`: `config.py`, `cli.py`, `requirements.txt`, `tests/test_cli.py`
  3. `chore: tach requirements dashboard, cau hinh VPS du phong (buoc 6)`: `dashboard/requirements.txt`, `deploy/`, `run_dashboard.sh`
  4. `feat: cau hinh trien khai Vercel (buoc 8-9)`: `api/`, `vercel.json`, `.vercelignore`, `.python-version`, `.gitignore`, `tests/test_vercel_config.py`
  5. `docs: cap nhat PLAN, PROGRESS, README, REPORT`
  Push lên nhánh `deploy/vercel`, mở PR vào `main` bằng `gh pr create`. Kiểm tra Vercel đã gắn link Preview vào PR (cần Vercel GitHub App có quyền vào repo; nếu chưa có thì 👤 người dùng cấp quyền ở Bước 11.1).

- [ ] **Q8 – 👤 Production (Bước 11).** Chỉ làm khi preview của PR pass `deploy/smoke_vercel.sh` **và** người dùng đồng ý merge. Merge xong thì chạy smoke test trên URL production, ghi URL và thời gian cold start/khi đã ấm vào `PROGRESS.md` và `REPORT.md`.

- [x] **Q9 – Bước 12 theo lựa chọn ở Q4.1.** Nếu chọn **b**, làm theo hướng dẫn đã sửa ở Bước 12: `middleware.ts` **không import thư viện ngoài**, vì `installCommand` chỉ chạy `npm ci` trong `dashboard/web`, nên `package.json` ở gốc sẽ không được cài.

- [x] **Q10 – Tài liệu (Bước 17).** Viết lại mục "Triển khai" trong `README.md` và `dashboard/README.md` theo Vercel. Phương án VPS chỉ còn một dòng trỏ tới phụ lục của `PLAN.md`. Ghi rõ: dữ liệu thật trên Vercel **chỉ nhận `.csv`** và nộp bằng cách commit vào `dashboard/data_real/`.

---

## A. HOÀN THIỆN CODE (Bước 1–6)

| Bước | Kết quả | Kiểm tra |
| :---: | :--- | :--- |
| 1 | `config.py` có đủ hằng số; `cli.py` tự dùng `sample_data_output1/annotations.xml` khi chưa có annotation | `.venv/bin/python cli.py` |
| 2 | 4 bộ test trong `tests/` | `.venv/bin/pytest tests/ -v` |
| 3 | 9 trang đăng ký trong `dashboard/api/pages/__init__.py` | `cd dashboard && ../.venv/bin/python -c "from api.pages import BUILDERS, PORTED; import catalog; assert len(BUILDERS) == 9; assert set(catalog.PAGES) <= PORTED"` |
| 4 | Icon đủ 11/11; **còn** `npm run typecheck` và bấm thử 11 trang (cần Node, xem Bước 7) | `cd dashboard/web && npm run typecheck` |
| 5 | `CVAT_*` có trong config, `python-dotenv` có trong requirements, `--no-mock-cvat`, `pyarrow` | `.venv/bin/python -c "import src.cvat_uploader"` |
| 6 | `dashboard/requirements.txt` chỉ chứa các gói của dashboard | xem Bước 8 (Vercel dùng file riêng, **bỏ pyarrow**) |

> Điều kiện để sang giai đoạn B: `.venv/bin/pytest tests/ -v` pass hết, và mọi `/api/pages/<path>?demo=true` trả về 200.

---

## B. CHUẨN BỊ

### Bước 7 – Node.js, Vercel CLI, tài khoản ⏳

1. **Cài Node.js ≥ 20** (khuyến nghị 22 LTS). Máy hiện tại **chưa có** `node`/`npm`. Node dùng để chạy `npm run typecheck`, `vercel dev`, và chạy CLI của Vercel. Bản build chính thức thì Vercel tự chạy trên cloud.
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
   sudo apt install -y nodejs
   node -v && npm -v
   ```
2. **Hoàn tất Bước 4:**
   ```bash
   cd dashboard/web && npm ci && npm run typecheck && npm run build
   ```
   Build xong phải có `dashboard/web/dist/index.html` và `dist/assets/*.js`.
3. **Vercel CLI:**
   ```bash
   npm i -g vercel
   vercel login            # đăng nhập bằng GitHub
   ```
4. **Tài khoản và quyền:**
   - Tạo tài khoản Vercel (gói Hobby miễn phí đủ cho đồ án) bằng GitHub của người sở hữu repo `caitoithap/T048_Build_phase`. Nếu repo thuộc organization thì cần cấp quyền cho Vercel GitHub App truy cập repo đó.
   - Lưu ý: gói Hobby **chỉ dùng phi thương mại** và chỉ có 1 thành viên. Muốn cả nhóm cùng quản lý project thì cần gói Pro, hoặc để một người làm chủ project còn những người khác deploy qua PR.

**Tiêu chí hoàn thành:** `vercel whoami` in ra tài khoản; `npm run build` thành công ở máy.

---

## C. CẤU HÌNH (chỉ thêm file mới, không sửa code hiện có)

### Bước 8 – Entry Python cho Vercel ⏳

Vercel coi mỗi file `.py` trong thư mục `api/` **ở gốc repo** là một function. Ta tạo đúng một function bọc app FastAPI có sẵn.

1. **`api/index.py`** (file mới ở gốc repo):
   ```python
   """Vercel Python Function: bọc app FastAPI của dashboard M22.

   Mọi request /api/* được vercel.json rewrite về đây. Code dashboard import theo kiểu
   `import settings`, `from api.pages import ...` (chạy từ thư mục dashboard/), nên cần đưa
   dashboard/ lên đầu sys.path trước khi import.
   """
   import sys
   from pathlib import Path

   DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard"
   sys.path.insert(0, str(DASHBOARD))
   # Thư mục api/ ở gốc repo (chứa chính file này) trùng tên với package dashboard/api.
   # Bỏ module "api" lỡ được nạp từ gốc, để import bên dưới lấy đúng dashboard/api.
   sys.modules.pop("api", None)

   from api.main import app  # noqa: E402  (Vercel tìm biến ASGI tên `app`)
   ```
   - **Trùng tên `api`:** `dashboard/api/` là package thường (có `__init__.py`), còn `api/` ở gốc thì không có `__init__.py`. Python ưu tiên package thường và `dashboard/` lại đứng đầu `sys.path`, nên import sẽ lấy đúng package. Dòng `sys.modules.pop` là chốt chặn thêm. **Phải xác minh ở Bước 10** (gọi `/api/meta` thành công là đã đúng).
   - Không cần `uvicorn`, vì Vercel tự chạy ASGI app.
2. **`api/requirements.txt`** (Vercel ưu tiên `requirements.txt` cùng thư mục với function. Nếu không có file này, Vercel sẽ cài `requirements.txt` gốc kèm torch và **vượt giới hạn 250 MB**):
   ```
   # Gói cho Vercel Function. Không có uvicorn (Vercel tự chạy ASGI), không có pyarrow (154 MB, vượt giới hạn).
   fastapi>=0.115.0
   pandas>=2.0.0
   numpy>=1.24.0
   altair>=6.0.0
   Pillow>=9.5.0
   ```
   Kiểm tra trong build log của Vercel: phải thấy cài từ `api/requirements.txt` và **không** thấy `torch`/`ultralytics`. Nếu Vercel vẫn lấy file gốc thì phương án dự phòng là đổi tên `requirements.txt` gốc thành `requirements-pipeline.txt` (khi đó phải cập nhật README và `run_dashboard.sh`).
3. **`.python-version`** ở gốc repo, ghi `3.12`, để chọn phiên bản Python của Vercel. Code đang chạy được trên 3.10 ở máy và không dùng cú pháp riêng của bản nào, nhưng **phải chạy lại test trên 3.12** trước khi deploy:
   ```bash
   python3.12 -m venv /tmp/m22-py312 && /tmp/m22-py312/bin/pip install -r api/requirements.txt pytest httpx
   cd dashboard && /tmp/m22-py312/bin/python -c "from fastapi.testclient import TestClient; from api.main import app; print(TestClient(app).get('/api/meta?demo=true').status_code)"
   ```

**Tiêu chí hoàn thành:** chạy giả lập ở máy `python -c "import runpy; m = runpy.run_path('api/index.py'); print(type(m['app']))"` in ra `<class 'fastapi.applications.FastAPI'>`.

### Bước 9 – `vercel.json` và `.vercelignore` ⏳

1. **`vercel.json`** ở gốc repo:
   ```json
   {
     "$schema": "https://openapi.vercel.sh/vercel.json",
     "framework": null,
     "installCommand": "cd dashboard/web && npm ci",
     "buildCommand": "cd dashboard/web && npm run build",
     "outputDirectory": "dashboard/web/dist",
     "regions": ["sin1"],
     "functions": {
       "api/index.py": {
         "maxDuration": 60,
         "includeFiles": "{sample_data_output1/annotations.xml,sample_data_output1/images.zip}",  // KHÔNG ghi dashboard/** (xem Q5 trong PROGRESS.md)
         "excludeFiles": "{dashboard/web/**,dashboard/views/**,**/__pycache__/**,_uv/**,.env*,.pytest_cache/**,src/**,tests/**,output/**,sample_data/**,deploy/**,*.pt,*.onnx,app.py,cli.py,config.py,run_dashboard.sh,README.md,REPORT.md,PLAN.md,PROGRESS.md,M22_*.md}"
       }
     },
     "rewrites": [
       { "source": "/api/(.*)", "destination": "/api/index" },
       { "source": "/(.*)", "destination": "/index.html" }
     ],
     "headers": [
       {
         "source": "/assets/(.*)",
         "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]
       }
     ]
   }
   ```
   Ý nghĩa từng phần:
   - `framework: null`, `installCommand`/`buildCommand`/`outputDirectory`: khai báo rõ frontend nằm trong `dashboard/web`. Việc đặt rõ cũng chặn Vercel tự nhận `app.py` ở gốc (Streamlit) là app Python.
   - `regions: ["sin1"]`: đặt function ở Singapore, gần Việt Nam nhất.
   - `includeFiles`: function cần `dashboard/` (code, `settings.py`, `catalog.py`, `data_real/`) và hai file dữ liệu `sample_data_output1/annotations.xml` + `images.zip`. Đường dẫn tính bằng `settings.py` (`PROJECT_DIR / "sample_data_output1"`) vẫn đúng vì Root Directory là gốc repo.
   - `excludeFiles`: bỏ `dashboard/web` (đã nằm trên CDN) và các trang Streamlit `views/` cho gói nhẹ hơn.
   - `rewrites`: rule `/api/(.*)` đứng trước nên mọi request API vào function. Rule `/(.*)` → `/index.html` là fallback cho SPA. Vercel ưu tiên file tĩnh có thật (như `/assets/...`) trước rewrite, nên file tĩnh không bị chặn. FastAPI vẫn nhận **đường dẫn gốc** (`/api/meta`…) nên route trong `dashboard/api/main.py` khớp mà không phải sửa. Điều này **phải xác minh ở Bước 10**.
   - `/docs` và `/openapi.json` của FastAPI nằm ngoài `/api/` nên rơi vào fallback SPA, tức là không bị lộ ra ngoài.
2. **`.vercelignore`** ở gốc repo (áp dụng cho cả deploy từ Git lẫn `vercel deploy` ở máy):
   ```
   # Cú pháp giống .gitignore: mẫu KHÔNG có "/" ở đầu thì khớp ở mọi cấp thư mục
   # (ví dụ "src/" sẽ xoá cả dashboard/web/src). Mục chỉ ở gốc repo phải viết "/" ở đầu.
   .venv/
   **/__pycache__/
   .pytest_cache/
   **/node_modules/
   /dashboard/web/dist/
   /output/
   /sample_data/
   /tests/
   /src/
   /app.py
   /cli.py
   /config.py
   *.pt
   *.onnx
   .env
   .env.*
   /deploy/
   /run_dashboard.sh
   ```
   Lý do: những thứ này thuộc pipeline YOLO, Streamlit hoặc VPS, function không dùng. Bỏ `app.py` đi còn tránh được việc Vercel nhận nhầm app Python.
   **Cẩn thận:** không được ghi `requirements.txt` hay `sample_data_output1/` vào file này, và **không** được bỏ `dashboard/web/src/`. Bản đầu tiên của kế hoạch ghi `src/` không có `/` đầu, nên đã xoá nhầm mã React (đã sửa ở Q1).

**Tiêu chí hoàn thành:** `vercel build` ở máy chạy xong và tạo `.vercel/output/` có `static/index.html` cùng `functions/api/index.func/`.
```bash
vercel pull --yes          # lấy cấu hình project (sau khi đã link ở Bước 10)
vercel build
du -sh .vercel/output/functions/api/index.func   # phải < 250 MB
```

---

## D. THỬ Ở MÁY VÀ PREVIEW

### Bước 10 – `vercel dev` và preview deployment ⏳

1. Liên kết thư mục với một project Vercel mới:
   ```bash
   cd "/media/trong-hung/New Volume/AITC/T048_Build_phase"
   vercel link              # tạo project mới, ví dụ tên m22-dashboard; Root Directory để "./"
   ```
   Lệnh này tạo thư mục `.vercel/`, cần thêm `.vercel` vào `.gitignore` (CLI thường tự thêm).
2. Chạy giả lập Vercel ở máy:
   ```bash
   vercel dev               # mở http://localhost:3000
   curl -fsS "http://localhost:3000/api/meta?demo=true" | head -c 300
   ```
3. Tạo bản preview (URL tạm, không ảnh hưởng tới production):
   ```bash
   vercel                   # in ra URL dạng https://m22-dashboard-xxxx.vercel.app
   ```
4. **Danh sách cần xác minh** (đây là các giả định ở Bước 8–9):
   - [ ] Build log có dòng cài từ `api/requirements.txt`, không có `torch`
   - [ ] Kích thước function < 250 MB (xem trong tab Deployment → Functions)
   - [ ] `GET /api/meta` trả về 200, tức là import `dashboard/api` đúng và không bị trùng tên `api`
   - [ ] `GET /api/pages/tong-quan?demo=true` trả về 200, tức là FastAPI nhận đúng path gốc sau rewrite
   - [ ] `GET /api/issues/<id>/crop.jpg` trả về ảnh, tức là `images.zip` đã được đóng gói kèm
   - [ ] F5 ở một trang con (ví dụ `/top-loi`) không trả 404
   - [ ] Không có lỗi `503 Không tìm thấy bộ đáp án`. Nếu có lỗi này thì `includeFiles` chưa đúng

**Nếu `/api/...` trả 404 từ FastAPI** (nghĩa là function nhận path `/api/index` thay vì path gốc): xem log để biết path thực tế mà function nhận được. Sau đó, trong `api/index.py`, bọc `app` bằng một ASGI middleware nhỏ khôi phục path gốc. Vẫn giữ nguyên `dashboard/api/main.py`.

---

## E. PRODUCTION

### Bước 11 – Project, domain, deploy production ⏳

1. Trên trang Vercel, vào **Project → Settings**:
   - **Git:** kết nối repo `caitoithap/T048_Build_phase`, Production Branch là `main`
   - **Root Directory:** `./` (gốc repo)
   - **Build & Development Settings:** để trống, vì `vercel.json` đã khai báo
   - **Node.js Version:** 22.x
   - **Environment Variables:** dashboard **không bắt buộc** biến nào. Không đặt `M22_REAL_DIR` (mặc định là `dashboard/data_real/`, xem Bước 14). `GEMINI_API_KEY`/`CVAT_*` **không** cần vì pipeline không chạy trên Vercel.
2. Commit các file cấu hình mới (`api/index.py`, `api/requirements.txt`, `.python-version`, `vercel.json`, `.vercelignore`) qua một PR, rồi xem preview của PR.
3. Merge vào `main` để Vercel tự deploy production. Hoặc chạy tay `vercel --prod`.
4. Domain: mặc định là `m22-dashboard.vercel.app`. Nếu có domain riêng thì vào **Settings → Domains**, thêm `m22.<domain-nhom>` và tạo bản ghi `CNAME` trỏ về `cname.vercel-dns.com`. Vercel tự cấp HTTPS.

**Tiêu chí hoàn thành:** URL production mở được trang Tổng quan qua HTTPS.

---

## F. BẢO VỆ TRUY CẬP

### Bước 12 – Giới hạn người xem ⏳

Dashboard không có đăng nhập. Ba lựa chọn, từ đơn giản đến chặt:

| Cách | Gói | Cách làm | Nhược điểm |
| :--- | :--- | :--- | :--- |
| **a. Để công khai** | Hobby | Không làm gì | Ai có link cũng xem được. Chấp nhận được nếu chỉ có dữ liệu giả hoặc dữ liệu BDD100K công khai |
| **b. Basic Auth bằng Routing Middleware** *(khuyến nghị)* | Hobby | Thêm `middleware.ts` ở gốc (mẫu bên dưới), kiểm tra header `Authorization` với biến môi trường `BASIC_AUTH_USER`/`BASIC_AUTH_PASS`, sai thì trả `401` kèm `WWW-Authenticate: Basic`. **Không** import `@vercel/functions`, vì `installCommand` chỉ cài trong `dashboard/web` | Thêm một ít code TypeScript; phải xác minh middleware chạy cả cho `/api/*` lẫn file tĩnh |
| **c. Password Protection của Vercel** | Pro (trả phí) | Settings → Deployment Protection → Password Protection | Tốn phí |

**Mẫu `middleware.ts` ở gốc repo (cách b):**
```ts
// Basic Auth cho toàn bộ site (trang tĩnh và /api). Chưa đặt hai biến môi trường thì không khoá.
// Không import thư viện: installCommand chỉ chạy npm ci trong dashboard/web.
export const config = { matcher: "/:path*" };

export default function middleware(request: Request): Response | undefined {
  const user = process.env.BASIC_AUTH_USER;
  const pass = process.env.BASIC_AUTH_PASS;
  if (!user || !pass) return undefined;
  const [scheme, encoded] = (request.headers.get("authorization") ?? "").split(" ");
  if (scheme === "Basic" && encoded && atob(encoded) === `${user}:${pass}`) return undefined;  // cho đi tiếp
  return new Response("Cần đăng nhập để xem dashboard M22.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="M22", charset="UTF-8"' },
  });
}
```
- Đặt biến (👤 người dùng cung cấp mật khẩu): `vercel env add BASIC_AUTH_USER production` và `vercel env add BASIC_AUTH_PASS production`. Làm tương tự cho `preview` nếu muốn.
- **Cần xác minh trên preview:** trả `undefined` thì request đi tiếp tới file tĩnh hoặc function. Nếu Vercel yêu cầu tín hiệu "đi tiếp" rõ ràng thì trả `new Response(null, { headers: { "x-middleware-next": "1" } })` (đây chính là thứ `next()` của `@vercel/functions` trả về).
- Middleware chạy trước rewrite, nên khoá được cả `/api/*`. Kiểm tra cả ba: `/`, `/top-loi`, `/api/meta`.
- Không thêm `middleware.ts` vào `.vercelignore`.

Ngoài ra nên bật **Vercel Authentication cho Preview Deployments** (miễn phí, mặc định đã bật) để link preview của PR không lộ ra ngoài.

**Kiểm tra (cách b):** `curl -I https://<url>/` trả 401; `curl -I -u user:pass https://<url>/` trả 200; `curl -u user:pass https://<url>/api/meta` trả 200.

---

## G. HIỆU NĂNG

### Bước 13 – Cold start và cache ⏳

1. **Cold start:** instance mới phải import pandas/altair rồi sinh dữ liệu giả (~3 s), nên request đầu tiên mất khoảng 4–6 s. Sau đó `lru_cache` trong `store.py` giữ kết quả cho tới khi instance bị thu hồi. Fluid Compute (mặc định với project mới) giúp tái sử dụng instance giữa các request.
2. **Giữ ấm (tuỳ chọn):** dùng UptimeRobot (miễn phí) gọi `https://<url>/api/meta?demo=true` mỗi 5 phút. Vercel Cron của gói Hobby chỉ chạy tối đa 1 lần/ngày nên không đủ để giữ ấm.
3. **Cache tĩnh:** `/assets/*` có header `immutable` (Bước 9). `index.html` thì Vercel mặc định không cache lâu, nên deploy mới có hiệu lực ngay.
4. **Không cache response API ở CDN:** dữ liệu phụ thuộc bộ lọc trên URL, và API đã tự đặt `Cache-Control: private` cho ảnh crop. Giữ nguyên.
5. **Theo dõi:** Vercel → Project → Observability/Logs, xem thời gian chạy và số lần cold start của `api/index.py`. Nếu thời gian vượt 10 s thường xuyên thì cân nhắc tăng `maxDuration` hoặc bỏ bớt trang nặng (`cham-cheo-annotator`).

---

## H. DỮ LIỆU THẬT

### Bước 14 – Cắm dữ liệu thật ⏳

Filesystem của Vercel Function **chỉ đọc và không bền vững**, nên **không thể** chép CSV lên server như VPS. Có hai cách:

1. **Commit CSV vào repo** *(khuyến nghị cho đồ án)*:
   - Pipeline (chạy ở máy cá nhân bằng `cli.py` hoặc các chặng A–G) xuất bảng theo đúng hợp đồng `dashboard/data_layer/schema.py`. Bộ mẫu tải ở `/api/sample.zip` hoặc trang **Nguồn dữ liệu**.
   - **Chỉ dùng `.csv`**, vì trên Vercel không có `pyarrow` để đọc `.parquet`.
   - Chép vào `dashboard/data_real/<tên bảng>.csv`, tạo PR, xem preview, rồi merge. Vercel tự deploy lại, và `includeFiles: dashboard/**` đã đóng gói thư mục này kèm function.
   - Thứ tự nộp theo `dashboard/README.md`: `issues` + `workload`, rồi các bảng so khớp chặng A, rồi `patches`, rồi `recommendations`.
   - **Lưu ý quyền riêng tư:** nếu repo công khai thì CSV cũng công khai. Không commit comment hay dữ liệu cá nhân thật; nếu cần thì chuyển repo sang private.
2. **Lưu trữ ngoài** (Vercel Blob, S3, Google Drive…), làm sau nếu cần cập nhật dữ liệu mà không phải deploy lại: cần sửa `dashboard/data_layer/store.py` để đọc từ URL. Việc này **ngoài phạm vi** kế hoạch này.

**Kiểm tra:** sau khi deploy, `/api/meta` trả `"mode": "real"` và `n_real` đúng số file; trang **Nguồn dữ liệu** báo đúng bảng đã có và chỉ ra giá trị lạ (nếu có). `?demo=true` vẫn xem được bản giả đầy đủ.

---

## I. KIỂM THỬ SAU TRIỂN KHAI

### Bước 15 – Smoke test ⏳

```bash
BASE=https://m22-dashboard.vercel.app; AUTH=""   # dùng Basic Auth thì: AUTH="-u t048:<mat-khau>"
curl -fsS $AUTH "$BASE/" -o /dev/null -w "index %{http_code}\n"
curl -fsS $AUTH "$BASE/top-loi" -o /dev/null -w "spa-fallback %{http_code}\n"
curl -fsS $AUTH "$BASE/api/meta" -o /dev/null -w "meta %{http_code} %{time_total}s\n"
curl -fsS $AUTH "$BASE/api/data-status" -o /dev/null -w "data-status %{http_code}\n"
curl -fsS $AUTH "$BASE/api/sample.zip" -o /dev/null -w "sample.zip %{http_code}\n"
for p in tong-quan top-loi class-kho annotator cham-cheo-annotator cham-cheo-reviewer sua-annotator sua-agent khuyen-nghi-pilot; do
  curl -fsS $AUTH "$BASE/api/pages/$p?demo=true" -o /dev/null -w "$p %{http_code} %{time_total}s\n"
  curl -fsS $AUTH "$BASE/api/pages/$p?demo=true&dark=true" -o /dev/null -w "$p dark %{http_code}\n"
done
ID=$(curl -fsS $AUTH "$BASE/api/issues?demo=true" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d)[:200])")
echo "$ID"
curl -fsS $AUTH "$BASE/docs" | grep -q swagger && echo "LỖI: /docs bị lộ" || echo "docs ẩn OK"
```

**Checklist thủ công:**
- [ ] Bấm qua 11 trang, không trang nào hiện "sắp có"
- [ ] Đổi bộ lọc (lô, class, cỡ, annotator), URL đổi theo; chép link sang tab khác vẫn giữ nguyên bộ lọc
- [ ] Chuyển sáng/tối, biểu đồ đổi màu theo
- [ ] Trang Chi tiết issue hiện ảnh crop có vẽ box
- [ ] Mở trên điện thoại (~400px) không vỡ bố cục
- [ ] Tải được bộ CSV mẫu ở trang Nguồn dữ liệu
- [ ] Lần mở đầu (cold start) < 10 s; các lần sau < 1 s

---

## J. VẬN HÀNH

### Bước 16 – Quy trình, log, rollback ⏳

1. **Quy trình thay đổi:** tạo nhánh, mở PR, GitHub đính kèm link **Preview** của Vercel. Chạy `.venv/bin/pytest tests/ -v` ở máy và smoke test (Bước 15) trên link preview, rồi merge vào `main` để có **Production**.
   - Có thể thêm GitHub Actions chạy `pytest` + `npm run typecheck` cho mỗi PR, để chặn merge khi test fail.
2. **Log:** Vercel → Project → **Logs** (lọc theo function `api/index.py`), hoặc dùng CLI:
   ```bash
   vercel logs <deployment-url>
   ```
3. **Rollback:** Vercel → Deployments → chọn bản cũ → **Instant Rollback** (gói Hobby lùi được về bản production liền trước). Hoặc dùng CLI:
   ```bash
   vercel rollback <deployment-url-cu>
   ```
   Sau đó revert commit lỗi trên `main`, để lần push sau không deploy lại lỗi đó.
4. **Giới hạn gói Hobby cần để ý:** số lần build mỗi ngày, băng thông và số lần gọi function mỗi tháng. Xem ở **Usage**. Với lượng truy cập của nhóm và lớp thì dư dả.
5. **Sao lưu:** mọi thứ (code + CSV thật) đã nằm trong Git, không cần sao lưu thêm.

---

## K. TÀI LIỆU

### Bước 17 – Cập nhật tài liệu 🟡
1. `README.md`: thêm mục "Triển khai Vercel" (link production, tóm tắt Bước 8–11, cách nộp dữ liệu ở Bước 14).
2. `dashboard/README.md`: thêm mục "Triển khai": vì sao có `api/index.py` ở gốc, quy định chỉ nhận `.csv` trên Vercel.
3. `REPORT.md`: ghi URL production, sơ đồ kiến trúc Vercel và kết quả smoke test (thời gian cold start và thời gian khi đã ấm).
4. Khi không còn cần bản Streamlit nữa thì xoá phần Streamlit của dashboard (`dashboard/app.py`, `views/`, `ui/components.py`, hai đoạn "cầu nối Streamlit" trong `store.py` và `theme.py`) theo `dashboard/README.md`. Lúc đó bỏ luôn `excludeFiles: dashboard/views/**`.

**Kiểm tra:** `pytest` pass hết; `git status` sạch; smoke test Bước 15 pass trên production.

---

## ⚠️ Rủi ro & lưu ý

| Rủi ro | Dấu hiệu | Cách xử lý |
| :--- | :--- | :--- |
| Vercel cài `requirements.txt` gốc (torch) | Build rất lâu, lỗi "function exceeds 250 MB" | Kiểm tra `api/requirements.txt` đúng chỗ; dự phòng đổi tên file gốc thành `requirements-pipeline.txt` |
| Cài `pyarrow` | Function vượt 250 MB | Không thêm `pyarrow` vào `api/requirements.txt`; chỉ nộp `.csv` |
| Import nhầm package `api` (thư mục gốc thay vì `dashboard/api`) | `ModuleNotFoundError: api.main` hoặc `api.pages` | `sys.path.insert(0, dashboard)` + `sys.modules.pop("api")` trong `api/index.py` |
| Thiếu file dữ liệu trong gói function | API trả `503 Không tìm thấy bộ đáp án`, ảnh crop 404 | Sửa `includeFiles`; kiểm tra `.vercelignore` không bỏ `sample_data_output1/` |
| Vercel nhận nhầm `app.py` (Streamlit) là app chính | Build lỗi khi import `streamlit` | `framework: null` + bỏ `app.py` trong `.vercelignore` |
| Cold start chậm | Lần đầu mở trang mất 4–6 s | Bước 13: giữ ấm bằng UptimeRobot |
| Chênh Python 3.10 (máy) với 3.12 (Vercel) | Lỗi chỉ xuất hiện trên Vercel | Chạy test bằng 3.12 (Bước 8.3) |
| Lộ dữ liệu thật khi repo công khai | CSV xem được trên GitHub | Chuyển repo sang private, hoặc chỉ commit dữ liệu đã ẩn danh |
| Số giả bị lẫn vào báo cáo | Trang có dải sọc hổ phách | Không trích số khi đang ở `demo=true` (xem `dashboard/README.md`) |
| Node/Vite/TS quá mới (Vite 8, TS 7) | `npm run build` lỗi trên Vercel | Đặt Node.js 22.x trong Settings; luôn `npm ci` theo `package-lock.json` |

---

## 📎 Phụ lục – Phương án dự phòng: VPS (Nginx + systemd)

Nếu Vercel không đáp ứng (vượt giới hạn gói, cần chạy cả pipeline YOLO, hoặc cần nhận file mà không deploy lại), có thể dùng VPS. Cấu hình đã có sẵn trong thư mục `deploy/`:

- `deploy/m22-api.service`: uvicorn chạy từ `dashboard/`, `M22_REAL_DIR=/opt/m22/data_real`, có warm-up sau khi khởi động
- `deploy/nginx-m22.conf`: phục vụ `dashboard/web/dist`, proxy `/api/` sang `127.0.0.1:8000`, SPA fallback
- `deploy/deploy.sh`: test, build, rsync và restart
- `deploy/.env.example`: biến môi trường mẫu

Tóm tắt: VPS Ubuntu 1–2 GB RAM, chạy `pip install -r dashboard/requirements.txt`, cài unit systemd, cài Nginx, rồi `certbot --nginx`. Dữ liệu thật thì rsync CSV vào `/opt/m22/data_real/`, không cần restart vì `store.py` cache theo `mtime`.

---

## 📝 Nhật ký tiến độ (Execution Progress)

- **Bước 1 (18/10/2026):**
  - Đã thêm các hằng số mặc định vào `config.py`: `DEFAULT_MODEL`, `DEFAULT_CONF_THRESHOLD`, `DEFAULT_MIN_BOX_SIZE`, `DEFAULT_MAX_BOX_ASPECT_RATIO`, `TARGET_CLASSES`.
  - Đã thêm cơ chế fallback tự động cho `cli.py`: nếu `output/pre_annotations_cvat.xml` chưa tồn tại, tự động nạp `sample_data_output1/annotations.xml`.
  - Đã kiểm tra khởi tạo `YOLOCPUDetector`, `QCFilter` và chạy lệnh `cli.py` thành công 100%.
- **Bước 2 (18/10/2026):**
  - Bổ sung phương thức `__contains__` cho dataclass `Tables` trong `dashboard/data_layer/store.py`.
  - Xây dựng 4 bộ test tự động: `tests/test_qc_rules.py`, `tests/test_data_layer.py`, `tests/test_api_endpoints.py`, `tests/test_cli.py`.
  - Chạy `pytest tests/ -v` đạt **15/15 test passed (100%)**.
- **Bước 3, 5, 6 (18/10/2026):** 9/9 trang trong `BUILDERS`; sửa các lỗi 5.1–5.4; tạo `dashboard/requirements.txt` và `deploy/` (VPS). Chi tiết ở `PROGRESS.md`.
- **Đổi hướng triển khai sang Vercel (18/10/2026):** viết lại các Bước 7–17 cho Vercel (Python Function + CDN tĩnh); phương án VPS chuyển xuống phụ lục. Số đo dùng để lập kế hoạch: sinh dữ liệu giả ~2,9 s; response lớn nhất ~51 KB; `sample.zip` ~532 KB; gói Python không có pyarrow ~135 MB (pyarrow riêng 154 MB).
