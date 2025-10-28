#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
DB="$ROOT/db/nysed.sqlite"
sqlite3 "$DB" < "$ROOT/baselines/baseline2_normalized/00_schema.sql"
sqlite3 "$DB" < "$ROOT/baselines/baseline2_normalized/10_load.sql"
echo "Baseline 2 (normalized, no indexes) built and loaded."
