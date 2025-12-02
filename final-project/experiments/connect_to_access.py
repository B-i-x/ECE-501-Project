import sqlite3, os, pathlib, pyodbc
import sqlalchemy as sa
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

#connecting to existing SRC2024_Group5 Access database using pyodbc
access_db = r"..\..\src\data\ny_edu_data\reportcard_database_23_24\SRC2024_Group5.accdb"
sqlite_db = r"..\data\nysed_clean.db"


con_string = (r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={access_db};")
#create SQLAlchemy engine object
con_url = URL.create("access+pyodbc", query={"odbc_connect": con_string})

try:
    engine = create_engine(con_url)
    #access_con = engine.connect()
    print(f"Connecting to Access database: {access_db}")
except SQLAlchemyError as e:
    print("Connection failed. Check if the Access Database Engine is installed.")
    raise e

# --- Connect to SQLite ---
sqlite_engine = create_engine(f"sqlite:///{sqlite_db}")


inspector = inspect(engine)
tables = [t for t in inspector.get_table_names() if not t.startswith("MSys")]
print(f"Found {len(tables)} user tables: {tables}\n")

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

# --- Transfer each table ---
for table in all_tables:
    # Skip Access system tables
    if table.startswith("MSys"):
        print(f"Skipping system table: {table}")
        continue

    try:
        print(f"Transferring table: {table} ...", end=" ")

        # Read data from Access
        df = pd.read_sql_table(table, engine)

        # Write to SQLite
        df.to_sql(table, sqlite_engine, index=False, if_exists="replace")

        print(f"✅ Done. Rows: {len(df)}")

    except Exception as e:
        print(f" Error transferring table {table}: {e}")

print("\n Migration complete!")
print(f"New SQLite database created at: {os.path.abspath(sqlite_db)}")

# --- Optional: verify a few tables in SQLite ---
verify_engine = create_engine(f"sqlite:///{sqlite_db}")
verify_inspect = inspect(verify_engine)
print("Tables now in SQLite:")
print(verify_inspect.get_table_names())

#df = pd.read_sql_table("SELECT * FROM Accountability Levels", con=engine)
#print(df.head())