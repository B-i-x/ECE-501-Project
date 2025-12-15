#!/usr/bin/env python3
"""
Normalize ONLY the header row in all CSVs under data_work/,
so SQLite .import-like logic won't choke on %, slashes, spaces, etc.
Works on Windows/macOS/Linux.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV_ROOT = ROOT / "data_work"

def normalize_header(h: str) -> str:
    h = re.sub(r"^\ufeff", "", h)         # strip BOM
    h = re.sub(r"\s+", "_", h)            # spaces -> _
    h = h.replace("%", "pct")             # % -> pct
    h = h.replace("/", "_")               # / -> _
    h = re.sub(r"[^A-Za-z0-9_,]", "_", h) # anything weird -> _
    h = re.sub(r"_{2,}", "_", h)          # collapse __
    h = re.sub(r"^_+|_+$", "", h)         # trim leading/trailing _
    return h

def fix_one(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not text:
        return
    header = text[0]
    fixed = normalize_header(header)
    if header != fixed:
        text[0] = fixed
        path.write_text("\n".join(text), encoding="utf-8")
        print(f"   - fixed header: {path.relative_to(ROOT)}")
    else:
        print(f"   - ok: {path.relative_to(ROOT)}")

def main():
    csvs = list(CSV_ROOT.rglob("*.csv"))
    if not csvs:
        print(f"No CSVs found under {CSV_ROOT}")
        return
    for c in csvs:
        fix_one(c)
    print("✅ Normalized CSV headers under data_work/")

if __name__ == "__main__":
    main()
