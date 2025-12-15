/* STAGING from normalized raw tables created by import_csv_to_sqlite.py
   Source tables in SQLite:
     acc_em_chronic_absenteeism
     annual_em_ela
     annual_em_math
     boces_n_rc
     expenditures_per_pupil

   This version:
   - Processes all data in source tables (filtering by source folder, not YEAR column)
   - Treats ELA/Math as Grades 3–8 combined (grade = 'All')
   - Treats attendance as school-level only (subgroup = 'All')
   
   Note: Data filtering is done at import time (only SRC2024 imported by default).
         The YEAR column in the data may not match the folder name (e.g., SRC2024 
         folder may contain data with YEAR='2023').
*/

DROP TABLE IF EXISTS st_years;
DROP TABLE IF EXISTS st_attendance_em_num;
DROP TABLE IF EXISTS st_assessment_em_num;
DROP TABLE IF EXISTS st_expenditures;
DROP TABLE IF EXISTS st_org;

-- Years present in source tables (all years in imported data)
CREATE TABLE st_years AS
SELECT DISTINCT CAST(YEAR AS INTEGER) AS year_key FROM acc_em_chronic_absenteeism
UNION
SELECT DISTINCT CAST(YEAR AS INTEGER) FROM annual_em_ela
UNION
SELECT DISTINCT CAST(YEAR AS INTEGER) FROM annual_em_math
UNION
SELECT DISTINCT CAST(YEAR AS INTEGER) FROM expenditures_per_pupil
WHERE YEAR IS NOT NULL;

-- ATTENDANCE
-- ABSENT_RATE is % absent; convert to absence_rate in [0,1]
-- Extract enrollment and absent_count from source table columns
CREATE TABLE st_attendance_em_num AS
SELECT
  CAST(YEAR AS INTEGER)                                AS year_key,
  ENTITY_CD                                           AS school_id,
  'All'                                               AS subgroup_raw,   -- no subgroup detail here
  CAST(NULLIF(ENROLLMENT,'s') AS INTEGER)             AS enrollment,
  CAST(NULLIF(ABSENT_COUNT,'s') AS INTEGER)           AS absent_count,
  CASE
    WHEN NULLIF(ABSENT_RATE,'s') IS NOT NULL
    THEN CAST(NULLIF(ABSENT_RATE,'s') AS REAL)/100.0
  END                                                 AS absence_rate,
  DATA_REP_FLAG,
  PARTIAL_DATA_FLAG,
  COUNT_ZERO_NON_DISPLAY_FLAG
FROM acc_em_chronic_absenteeism;

-- ASSESSMENT (ELA + Math)
-- We set grade = 'All' because the table is already an aggregate (no per-grade column)
CREATE TABLE st_assessment_em_num AS
SELECT
  CAST(YEAR AS INTEGER)                                AS year_key,
  ENTITY_CD                                           AS school_id,
  TRIM(SUBGROUP_NAME)                                 AS subgroup_raw,
  'ELA'                                               AS subject,
  'All'                                               AS grade,
  CAST(NULLIF(NUM_TESTED,'s') AS INTEGER)             AS tested,
  (CAST(NULLIF(LEVEL3_COUNT,'s') AS INTEGER)
   + CAST(NULLIF(LEVEL4_COUNT,'s') AS INTEGER))       AS n_qual,
  CASE
    WHEN NULLIF(LEVEL3_pctTESTED,'s') IS NOT NULL
     AND NULLIF(LEVEL4_pctTESTED,'s') IS NOT NULL
    THEN (CAST(NULLIF(LEVEL3_pctTESTED,'s') AS REAL)
        + CAST(NULLIF(LEVEL4_pctTESTED,'s') AS REAL)) / 100.0
  END                                                 AS qual_rate
FROM annual_em_ela
UNION ALL
SELECT
  CAST(YEAR AS INTEGER)                                AS year_key,
  ENTITY_CD                                           AS school_id,
  TRIM(SUBGROUP_NAME)                                 AS subgroup_raw,
  'Math'                                              AS subject,
  'All'                                               AS grade,
  CAST(NULLIF(NUM_TESTED,'s') AS INTEGER)             AS tested,
  (CAST(NULLIF(LEVEL3_COUNT,'s') AS INTEGER)
   + CAST(NULLIF(LEVEL4_COUNT,'s') AS INTEGER))       AS n_qual,
  CASE
    WHEN NULLIF(LEVEL3_pctTESTED,'s') IS NOT NULL
     AND NULLIF(LEVEL4_pctTESTED,'s') IS NOT NULL
    THEN (CAST(NULLIF(LEVEL3_pctTESTED,'s') AS REAL)
        + CAST(NULLIF(LEVEL4_pctTESTED,'s') AS REAL)) / 100.0
  END                                                 AS qual_rate
FROM annual_em_math;

-- EXPENDITURES (school-level per-pupil expenditure)
CREATE TABLE st_expenditures AS
SELECT
  CAST(YEAR AS INTEGER)                                AS year_key,
  ENTITY_CD                                           AS school_id,
  CAST(NULLIF(PER_FED_STATE_LOCAL_EXP,'s') AS REAL)  AS per_pupil_expenditure,
  DATA_REPORTED_EXP,
  DATA_REPORTED_ENR
FROM expenditures_per_pupil
WHERE DATA_REPORTED_EXP = 'Y'
  AND DATA_REPORTED_ENR = 'Y'
  AND PER_FED_STATE_LOCAL_EXP IS NOT NULL
  AND PER_FED_STATE_LOCAL_EXP != 's';

-- ORG lookup
CREATE TABLE st_org AS
SELECT
  ENTITY_CD      AS school_id,
  SCHOOL_NAME    AS school_name,
  DISTRICT_CD    AS district_id,
  DISTRICT_NAME  AS district_name,
  COUNTY_NAME,
  NEEDS_INDEX    AS needs_index,
  NEEDS_INDEX_DESCRIPTION AS needs_index_description
FROM boces_n_rc;

-- Subgroup mapping table (persistent, if not already present)
CREATE TABLE IF NOT EXISTS map_subgroups (
  raw_label   TEXT PRIMARY KEY,
  subgroup_id TEXT,
  subgroup_name TEXT
);
