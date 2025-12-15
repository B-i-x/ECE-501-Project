#!/usr/bin/env python3
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "etl" / "map_subgroups.csv"

def canon(s: str) -> str:
    """Canonical form of a label: lowercase, strip non-letters/digits."""
    s = s.lower().strip()
    # remove punctuation and spaces
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def main():
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    # 1) Build canonical map from rows that already have subgroup_id
    canon_to_idname = {}
    for r in rows:
        raw = r["raw_label"].strip()
        sid = (r.get("subgroup_id") or "").strip()
        sname = (r.get("subgroup_name") or "").strip()
        if raw and sid:
            canon_to_idname[canon(raw)] = (sid, sname or raw)

    # 2) Add explicit synonym rules (map canonical raw -> canonical known)
    synonyms = {
        canon("All"): canon("All Students"),
        canon("Black or African American"): canon("Black"),
        canon("Hispanic or Latino"): canon("Hispanic"),
        canon("Asian or Native Hawaiian/Other Pacific Islander"): canon("Asian_NHPI"),
        canon("English Language Learner"): canon("English Language Learners"),
    }

    # 3) Fill missing subgroup_id / subgroup_name where possible
    for r in rows:
        raw = r["raw_label"].strip()
        if not raw:
            continue

        if r.get("subgroup_id"):  # already filled
            continue

        c = canon(raw)
        # synonym indirection
        if c in synonyms:
            c = synonyms[c]

        sid_sname = canon_to_idname.get(c)
        if sid_sname is not None:
            sid, sname = sid_sname
            r["subgroup_id"] = sid
            r["subgroup_name"] = sname
            continue

        # 4) Simple auto-codes for one-off groups (manual list)        
        auto_codes = {
            "allstudents": ("All", "All Students"),
            "asian": ("Asian", "Asian"),
            "asiannhpi": ("Asian_NHPI", "Asian or NHPI"),
            "nativehawaiianorotherpacificislander": ("NHPI", "Native Hawaiian or Other Pacific Islander"),
            "americanindianoralaskanative": ("AIAN", "American Indian or Alaska Native"),
            "black": ("Black", "Black"),
            "hispanic": ("Hispanic", "Hispanic"),
            "white": ("White", "White"),
            "multiracial": ("Multiracial", "Multiracial"),
            "studentswithdisabilities": ("SWD", "Students with Disabilities"),
            "economicallydisadvantaged": ("ED", "Economically Disadvantaged"),
            "noteconomicallydisadvantaged": ("NotED", "Not Economically Disadvantaged"),
            "englishlanguagelearners": ("ELL", "English Language Learners"),
            "nonenglishlanguagelearner": ("NonELL", "Non-English Language Learner"),
            "generaleducationstudents": ("GenEd", "General Education Students"),
            "homeless": ("Homeless", "Homeless"),
            "nothomeless": ("NotHomeless", "Not Homeless"),
            "infostercare": ("Foster", "In Foster Care"),
            "notinfostercare": ("NotFoster", "Not in Foster Care"),
            "migrant": ("Migrant", "Migrant"),
            "notmigrant": ("NotMigrant", "Not Migrant"),
            "parentinarmedforces": ("ParentMilitary", "Parent in Armed Forces"),
            "parentnotinarmedforces": ("ParentNotMilitary", "Parent Not in Armed Forces"),
            "female": ("F", "Female"),
            "male": ("M", "Male"),
            "nonbinary": ("NB", "Non-Binary"),
        }


        if c in auto_codes:
            sid, sname = auto_codes[c]
            r["subgroup_id"] = sid
            r["subgroup_name"] = sname
            continue

        # 5) Leave truly ambiguous/meta ones blank for manual handling
        # e.g. "Asian or Native Hawaiian/Other Pacific Islander",
        #      "Small Group Total: Gender", etc.

    # 6) Write back the updated CSV (backup first if you want)
    backup_path = CSV_PATH.with_suffix(".csv.bak")
    if not backup_path.exists():
        backup_path.write_text(CSV_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {CSV_PATH}")
    print(f"Original backed up at {backup_path}")

if __name__ == "__main__":
    main()
