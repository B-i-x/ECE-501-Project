#!/usr/bin/env python3
"""
Clean & standardize NYSED CSVs:
- Canonicalize subgroup labels via etl/map_subgroups.csv
- Ensure all rates are proportions in [0,1]
- Trim/uppercase IDs; strip whitespace
Writes cleaned CSVs to data_work/.
"""
import os, sys, csv, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_RAW  = ROOT / "data_raw"
DATA_WORK = ROOT / "data_work"
MAP_FILE  = ROOT / "etl" / "map_subgroups.csv"

# Configure input patterns (adjust to your filenames)
FILES = {
    "enrollment": {"pattern": "enrollment*.csv"},
    "attendance": {"pattern": "attendance*.csv"},
    "assessment": {"pattern": "assessment*.csv"},  # should include grades 3-8 ELA/Math
}

# Columns that should be rates (scaled to 0..1 if they look like percentages)
RATE_COLS = {
    "attendance": ["absence_rate"],
    "assessment": ["qual_rate"],
}

# Minimal required columns we expect to find (rename your raw columns to these)
RENAME_MAPS = {
    "enrollment": {
        # raw -> standard
        "YEAR": "year",
        "SCHOOL_ID": "school_id",
        "DISTRICT_ID": "district_id",
        "SUBGROUP": "subgroup_raw",
        "NUMBER_STUDENTS": "n_students",
    },
    "attendance": {
        "YEAR": "year",
        "SCHOOL_ID": "school_id",
        "DISTRICT_ID": "district_id",
        "SUBGROUP": "subgroup_raw",
        "ABSENCE_RATE": "absence_rate",
        "ATTENDANCE_INDICATOR": "attendance_indicator",
    },
    "assessment": {
        "YEAR": "year",
        "SCHOOL_ID": "school_id",
        "DISTRICT_ID": "district_id",
        "SUBGROUP": "subgroup_raw",
        "SUBJECT": "subject",
        "GRADE": "grade",
        "TESTED": "tested",
        "N_QUAL": "n_qual",
        "QUAL_RATE": "qual_rate",
    },
}

def load_subgroup_map():
    mp = pd.read_csv(MAP_FILE, dtype=str).fillna("")
    mp["raw_label"]    = mp["raw_label"].str.strip()
    mp["subgroup_id"]  = mp["subgroup_id"].str.strip()
    mp["subgroup_name"]= mp["subgroup_name"].str.strip()
    return mp

def canonicalize_subgroup(df, mp):
    df["subgroup_raw"] = df["subgroup_raw"].astype(str).str.strip()
    df = df.merge(mp.rename(columns={"raw_label":"subgroup_raw"}), on="subgroup_raw", how="left")
    # If no map hit, carry over the raw label as id/name for now
    df["subgroup_id"]   = df["subgroup_id"].fillna(df["subgroup_raw"])
    df["subgroup_name"] = df["subgroup_name"].fillna(df["subgroup_raw"])
    return df

def scale_rates(df, rate_cols):
    for c in rate_cols:
        if c in df.columns:
            # force float, coerce errors to NaN
            df[c] = pd.to_numeric(df[c], errors="coerce")
            # if any values look like percentages (>1.0), assume 0-100 and scale
            if df[c].dropna().gt(1).any():
                df[c] = df[c] / 100.0
            # clamp to [0,1] where not null
            df[c] = df[c].clip(lower=0, upper=1)
    return df

def normalize_ids(df):
    for col in ("school_id","district_id"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df

def clean_file(kind, path, mp):
    df = pd.read_csv(path, dtype=str)
    # rename columns to standard names (only those present)
    rename = {k:v for k,v in RENAME_MAPS[kind].items() if k in df.columns}
    df = df.rename(columns=rename)

    # sanity keep only columns we care about
    keep = list(RENAME_MAPS[kind].values())
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    df = normalize_ids(df)
    df = canonicalize_subgroup(df, mp)

    if kind in RATE_COLS:
        df = scale_rates(df, RATE_COLS[kind])

    # minimal filters: keep Grades 3-8 and ELA/Math for assessment
    if kind == "assessment":
        if "grade" in df.columns:
            df = df[df["grade"].isin(["3","4","5","6","7","8","All"])]
        if "subject" in df.columns:
            df = df[df["subject"].isin(["ELA","Math","ELA/Math","All"])]

    out = DATA_WORK / f"clean_{kind}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"[clean] wrote {out} ({len(df):,} rows)")

def main():
    mp = load_subgroup_map()
    for kind, conf in FILES.items():
        pattern = conf["pattern"]
        # pick the newest matching file; adjust if you want >1
        matches = sorted(DATA_RAW.glob(pattern))
        if not matches:
            print(f"[warn] no files for {kind} matching {pattern}")
            continue
        clean_file(kind, matches[-1], mp)

if __name__ == "__main__":
    main()
