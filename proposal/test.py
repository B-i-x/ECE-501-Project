import sqlite3
import pandas as pd
import pyodbc
from collections import Counter

DATA_PATH = r"data\ny_edu_data\enrollment_database_23_24\ENROLL2024_20241105.accdb"

src = pyodbc.connect(rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DATA_PATH};")
dst = sqlite3.connect("data/sqlite/enrollment2024.db")

cur = src.cursor()

# Enumerate ALL objects; don't restrict by tableType
rows = list(cur.tables())

# Keep real stuff; skip Access system/temp objects
ALLOW_TYPES = {"TABLE", "VIEW", "SYSTEM TABLE"}
def wanted(r):
    name = (r.table_name or "").strip()
    if not name:
        return False
    # Skip system & temp
    if name.startswith("MSys") or name.startswith("~"):
        return False
    return (r.table_type or "").upper() in ALLOW_TYPES

objs = [r for r in rows if wanted(r)]

# Show what we found by type
counts = Counter((r.table_type or "UNKNOWN").upper() for r in objs)
print("Discovered objects:", counts)

# Dedup by name (Access can return duplicates with different schema/catalog)
seen = set()
tables = []
for r in objs:
    nm = r.table_name
    if nm not in seen:
        seen.add(nm)
        tables.append(nm)

print(f"Will attempt to copy {len(tables)} objects:")
for nm in tables:
    print(" -", nm)

# Copy loop
copied, skipped = [], []
for t in tables:
    try:
        # Some Access "VIEWs" (saved queries) can be parameterized or call VBA functions;
        # those will fail over ODBC—catch and skip them.
        df = pd.read_sql(f"SELECT * FROM [{t}]", src)
        df.to_sql(t, dst, if_exists='replace', index=False)
        copied.append(t)
        print(f"✔ Copied: {t} ({len(df)} rows)")
    except Exception as e:
        skipped.append((t, str(e)))
        print(f"✖ Skipped: {t} -> {e}")

dst.close(); src.close()

print("\nSummary:")
print(f"Copied: {len(copied)}")
if skipped:
    print(f"Skipped: {len(skipped)}")
    for name, err in skipped:
        print(f" - {name}: {err}")
