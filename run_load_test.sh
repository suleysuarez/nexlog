#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BASE_URL="${BASE_URL:-http://host.docker.internal:8000/api/v1}"
K6_IMAGE="${K6_IMAGE:-grafana/k6}"
K6_SCRIPT="${K6_SCRIPT:-k6/k6_script.js}"

echo "==> Building API image"
docker compose build api

echo "==> Starting MongoDB and API"
docker compose up -d mongodb api

echo "==> Running mandatory seed before load test"
docker compose exec api python scripts/seed.py

echo "==> Running k6 mixed-scenarios load test"
if [[ "$(uname -s)" =~ MINGW|MSYS|CYGWIN ]]; then
  HOST_PWD="$(pwd -W)"
  MSYS2_ARG_CONV_EXCL='*' docker run --rm -i \
    -v "${HOST_PWD}:/app" \
    -e BASE_URL="${BASE_URL}" \
    "${K6_IMAGE}" run "/app/${K6_SCRIPT}"
else
  docker run --rm -i \
    -v "${PWD}:/app" \
    -e BASE_URL="${BASE_URL}" \
    "${K6_IMAGE}" run "/app/${K6_SCRIPT}"
fi
