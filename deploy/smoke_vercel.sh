#!/usr/bin/env bash
# Smoke test bản triển khai Vercel (Bước 15 của PLAN.md). Trả mã ≠ 0 nếu có request nào không đạt.
#   deploy/smoke_vercel.sh https://m22-dashboard.vercel.app
#   deploy/smoke_vercel.sh https://<preview-url> t048:<mat-khau>     # khi bật Basic Auth
# Preview bị Vercel Authentication khoá: chạy qua vercel env run để có VERCEL_OIDC_TOKEN (token ngắn hạn, không in ra)
#   vercel env run -- deploy/smoke_vercel.sh https://<preview-url>
# hoặc dùng secret "Protection Bypass for Automation":
#   VERCEL_BYPASS=<secret> deploy/smoke_vercel.sh https://<preview-url>
set -uo pipefail
BASE=${1:?dùng: smoke_vercel.sh BASE [USER:PASS]}
BASE=${BASE%/}
ARGS=(-sS --max-time 90)
[ -n "${2:-}" ] && ARGS+=(-u "$2")
[ -n "${VERCEL_BYPASS:-}" ] && ARGS+=(-H "x-vercel-protection-bypass: $VERCEL_BYPASS")
[ -n "${VERCEL_OIDC_TOKEN:-}" ] && ARGS+=(-H "x-vercel-trusted-oidc-idp-token: $VERCEL_OIDC_TOKEN")
FAIL=0

check() {  # check <tên> <đường dẫn> [content-type mong đợi]
  local out code type secs
  out=$(curl "${ARGS[@]}" -o /dev/null -w "%{http_code} %{time_total} %{content_type}" "$BASE$2") || out="000 0 -"
  read -r code secs type <<<"$out"
  if [ "$code" != 200 ] || { [ -n "${3:-}" ] && [[ "$type" != "$3"* ]]; }; then
    printf "FAIL %-28s %s %s\n" "$1" "$code" "$type"; FAIL=1
  else
    printf "ok   %-28s %s %ss\n" "$1" "$code" "$secs"
  fi
}

check index / text/html
check spa-fallback /top-loi text/html
check meta /api/meta application/json
check data-status /api/data-status application/json
check sample.zip /api/sample.zip application/zip
for p in tong-quan top-loi class-kho annotator cham-cheo-annotator cham-cheo-reviewer sua-annotator sua-agent khuyen-nghi-pilot; do
  check "$p" "/api/pages/$p?demo=true" application/json
  check "$p dark" "/api/pages/$p?demo=true&dark=true" application/json
done

ID=$(curl "${ARGS[@]}" "$BASE/api/issues?demo=true" | python3 -c "import json,sys; print(json.load(sys.stdin)['items'][0]['id'])" 2>/dev/null)
if [ -n "$ID" ]; then
  check "issue $ID" "/api/issues/$ID?demo=true" application/json
  check "crop $ID" "/api/issues/$ID/crop.jpg?demo=true" image/jpeg
else
  echo "FAIL không lấy được issue_id từ /api/issues"; FAIL=1
fi

# /docs của FastAPI nằm ngoài /api/ nên phải rơi vào trang SPA, không được là Swagger.
if curl "${ARGS[@]}" "$BASE/docs" | grep -qi swagger; then echo "FAIL /docs bị lộ"; FAIL=1; else echo "ok   docs ẩn"; fi

[ "$FAIL" = 0 ] && echo "SMOKE OK" || echo "SMOKE FAIL"
exit "$FAIL"
