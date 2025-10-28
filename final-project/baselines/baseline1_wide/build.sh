#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
DB="$ROOT/db/nysed.sqlite"
sqlite3 "$DB" < "$ROOT/baselines/baseline1_wide/00_schema.sql"
sqlite3 "$DB" < "$ROOT/baselines/baseline1_wide/10_load.sql"
echo "Baseline 1 (wide) built and loaded."
