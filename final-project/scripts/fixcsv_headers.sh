# scripts/fixcsv_headers.sh
#!/usr/bin/env bash
set -euo pipefail

# Edit first line only (header): strip BOM, spaces->_, %->pct, /->_, nonword->_, collapse __, trim _.
fix_one() {
  local f="$1"
  # Read first line, transform, then write back with the rest untouched
  local header rest tmp
  header="$(head -n 1 "$f" | sed -E $'s/^\xEF\xBB\xBF//; s/[[:space:]]+/_/g; s/%/pct/g; s|/|_|g; s/[^A-Za-z0-9_,]/_/g; s/_{2,}/_/g; s/^_+//; s/_+$//;')"
  # macOS/BSD compatible tail -n +2
  tmp="$(mktemp)"
  { echo "$header"; tail -n +2 "$f"; } > "$tmp"
  mv "$tmp" "$f"
}

export -f fix_one

# Walk all CSVs under data_work
find data_work -type f -name "*.csv" -print0 | xargs -0 -I {} bash -c 'fix_one "$@"' _ {}
echo "Normalized CSV headers under data_work/."
