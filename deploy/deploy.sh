#!/usr/bin/env bash
# Cập nhật bản triển khai. Chạy trên máy build, từ thư mục gốc repo, sau khi đã gắn tag vYYYY.MM.DD-N lên main.
#   SERVER=user@host deploy/deploy.sh
# Rollback:
#   ssh <server> "sudo -u m22 git -C /opt/m22/app checkout <tag-cu> && sudo rm -rf /opt/m22/web \
#     && sudo mv /opt/m22/web.prev /opt/m22/web && sudo systemctl restart m22-api"
set -euo pipefail
SERVER=${SERVER:?đặt SERVER=user@host}
TAG=$(git describe --tags --always)

.venv/bin/pytest tests/ -q                              # test fail thì dừng
(cd dashboard/web && npm ci && npm run build)

ssh "$SERVER" "sudo -u m22 git -C /opt/m22/app fetch --tags && sudo -u m22 git -C /opt/m22/app checkout $TAG \
  && sudo -u m22 /opt/m22/venv/bin/pip install -q -r /opt/m22/app/dashboard/requirements.txt \
  && sudo rm -rf /opt/m22/web.prev && sudo cp -a /opt/m22/web /opt/m22/web.prev"
rsync -avz --delete dashboard/web/dist/ "$SERVER":/opt/m22/web/
ssh "$SERVER" "sudo systemctl restart m22-api && sleep 5 && curl -fsS -o /dev/null http://127.0.0.1:8000/api/meta && echo OK $TAG"
