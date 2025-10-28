# macOS/BSD sed: edit CSVs in place, only the FIRST line (header)
find data_work -type f -name "*.csv" -print0 | xargs -0 -I {} \
  sed -i '' -E '1{
    s/^\xEF\xBB\xBF//;         # strip BOM if present
    s/[[:space:]]+/_/g;        # spaces -> _
    s/%/pct/g;                 # % -> pct
    s/\//_/g;                  # / -> _
    s/[^A-Za-z0-9_,]/_/g;      # anything weird -> _
    s/_{2,}/_/g;               # collapse __
    s/^_+//; s/_+$//;          # trim leading/trailing _
  }' "{}"
