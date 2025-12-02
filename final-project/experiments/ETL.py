"""
ETL: Access → SQLite (NYSED Star Schema)
----------------------------------------
1. Creates schema (from 00_schema.sql)
2. Connects to Access (.accdb)
3. Reads tables per SRC2024ReadMe_Group5.pdf
4. Maps and renames columns for star schema
5. Loads data into SQLite with surrogate key lookups
"""

import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# ========= USER CONFIG =========
ACCESS_FILE = r"../../src/data/ny_edu_data/reportcard_database_23_24/SRC2024_Group5.accdb"
SQLITE_FILE = r"../data/nysed_clean.db"
SCHEMA_FILE = r"../sql/00_schema.sql"
# ===============================

# ---------- STEP 1: BUILD STAR SCHEMA ----------
sqlite_engine = create_engine(f"sqlite:///{SQLITE_FILE}", echo=False)
print("🧱 Creating star schema in SQLite...")
with open(SCHEMA_FILE, "r") as f:
    schema_sql = f.read()
with sqlite_engine.begin() as conn:
    conn.execute(text(schema_sql))
print("✅ Schema created successfully.\n")

# ---------- STEP 2: CONNECT TO ACCESS ----------
access_conn_str = (
    "access+pyodbc:///?odbc_connect="
    "Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={ACCESS_FILE};"
)
try:
    print(f"🔗 Connecting to Access database: {ACCESS_FILE}")
    access_engine = create_engine(access_conn_str)
except SQLAlchemyError as e:
    print("❌ Connection failed. Ensure Microsoft Access Database Engine is installed.")
    raise e

insp = inspect(access_engine)
tables = [t for t in insp.get_table_names() if not t.startswith("MSys")]
print(f"✅ Found {len(tables)} user tables: {tables}\n")

# ---------- STEP 3: DEFINE COLUMN MAPPINGS ----------
column_mappings = {
    "BOCES_and_NRC": {
        "DISTRICT_CD": "district_id",
        "DISTRICT_NAME": "district_name",
        "COUNTY_NAME": "county_name",
        "NEEDS_INDEX": "nrc_code",
        "NEEDS_INDEX_DESCRIPTION": "nrc_desc",
    },
    "Institution_Grouping": {
        "ENTITY_CD": "school_id",
        "ENTITY_NAME": "school_name",
    },
    "ACC_EM_Chronic_Absenteeism": {
        "YEAR": "year_key",
        "ENTITY_CD": "school_id",
        "SUBGROUP_NAME": "subgroup_id",
        "ABSENT_COUNT": "absent_count",
        "ABSENT_RATE": "absence_rate",
        "ENROLLMENT": "enrollment",
        "DATA_REP_FLAG": "data_rep_flag",
        "PARTIAL_DATA_FLAG": "partial_data_flag",
        "COUNT_ZERO_NON_DISPLAY_FLAG": "count_zero_flag",
    },
    "Annual_EM_ELA": {
        "YEAR": "year_key",
        "ENTITY_CD": "school_id",
        "ASSESSMENT_NAME": "grade_id",
        "SUBGROUP_NAME": "subgroup_id",
        "NUM_TESTED": "tested",
        "NUM_PROF": "n_qual",
        "PER_PROF": "qual_rate",
    },
    "Annual_EM_Math": {
        "YEAR": "year_key",
        "ENTITY_CD": "school_id",
        "ASSESSMENT_NAME": "grade_id",
        "SUBGROUP_NAME": "subgroup_id",
        "NUM_TESTED": "tested",
        "NUM_PROF": "n_qual",
        "PER_PROF": "qual_rate",
    },
}

# ---------- STEP 4: UTILITY FUNCTIONS ----------

def insert_dim_unique(df, table, conn, key_col, name_col=None):
    """
    Inserts unique values into dimension tables and returns lookup dictionary {source_value: surrogate_key}.
    """
    df_unique = df[[key_col]].drop_duplicates().dropna()
    df_unique.reset_index(drop=True, inplace=True)
    if name_col and name_col in df.columns:
        df_unique[name_col] = df[name_col]
    df_unique.to_sql(table, conn, if_exists="append", index=False)
    lookup = pd.read_sql(f"SELECT {key_col}, rowid as key FROM {table}", conn)
    return dict(zip(lookup[key_col], lookup["key"]))

def lookup_key(value, mapping):
    """Safe lookup with fallback."""
    return mapping.get(value, None)

# ---------- STEP 5: LOAD DIMENSIONS ----------
with sqlite_engine.begin() as conn:
    # Load District dimension
    if "BOCES_and_NRC" in tables:
        df_district = pd.read_sql_table("BOCES_and_NRC", access_engine)
        df_district = df_district.rename(columns=column_mappings["BOCES_and_NRC"])
        df_district = df_district[list(column_mappings["BOCES_and_NRC"].values())]
        df_district.to_sql("dim_district", conn, if_exists="append", index=False)
        print(f"✅ Loaded {len(df_district)} rows into dim_district.")

    # Load School dimension
    if "Institution_Grouping" in tables:
        df_school = pd.read_sql_table("Institution_Grouping", access_engine)
        df_school = df_school.rename(columns=column_mappings["Institution_Grouping"])
        df_school = df_school[list(column_mappings["Institution_Grouping"].values())]
        # Add foreign key mapping for district
        df_school["district_key"] = 1  # Placeholder: match via district_id if available
        df_school.to_sql("dim_school", conn, if_exists="append", index=False)
        print(f"✅ Loaded {len(df_school)} rows into dim_school.")

    # Load Year dimension
    df_year = pd.DataFrame({"year_key": [2023, 2024], "school_year_label": ["2022-23", "2023-24"]})
    df_year.to_sql("dim_year", conn, if_exists="append", index=False)
    print("✅ Loaded dim_year with 2023–2024 sample years.\n")

# ---------- STEP 6: LOAD FACT TABLES ----------
for table, mapping in column_mappings.items():
    if table not in tables or not table.startswith(("ACC_", "Annual_")):
        continue

    print(f"📦 Transforming {table} → fact table")
    try:
        df = pd.read_sql_table(table, access_engine)
        df = df.rename(columns=mapping)
        df = df[list(mapping.values())]

        if table.startswith("ACC_EM_Chronic_Absenteeism"):
            target = "fact_attendance"
        elif table.startswith("Annual_EM_"):
            target = "fact_assessment"
        else:
            continue

        df.to_sql(target, sqlite_engine, if_exists="append", index=False)
        print(f"✅ Loaded {len(df)} rows into {target}\n")

    except Exception as e:
        print(f"❌ Error loading {table}: {e}\n")

print("🎉 ETL completed successfully.")
print(f"SQLite star schema database: {os.path.abspath(SQLITE_FILE)}")