/* STAGING from normalized raw tables created by import_csv_to_sqlite.sh
   Source tables in SQLite:
     acc_em_chronic_absenteeism
     annual_em_ela
     annual_em_math
     boces_n_rc
*/

DROP TABLE IF EXISTS st_years;
DROP TABLE IF EXISTS st_attendance_em_num;
DROP TABLE IF EXISTS st_assessment_em_num;
DROP TABLE IF EXISTS st_org;

-- Years from any of the three sources
CREATE TEMP TABLE st_years AS
SELECT DISTINCT CAST(YEAR AS INTEGER) AS year_key FROM acc_em_chronic_absenteeism
UNION
SELECT DISTINCT CAST(YEAR AS INTEGER) FROM annual_em_ela
UNION
SELECT DISTINCT CAST(YEAR AS INTEGER) FROM annual_em_math;

-- ATTENDANCE (percent -> proportion)
CREATE TEMP TABLE st_attendance_em_num AS
SELECT
  CAST(YEAR AS INTEGER)                                AS year_key,
  ENTITY_CD                                           AS school_id,
  INSTITUTION_ID                                      AS institution_id,
  TRIM(SUBGROUP_NAME)                                 AS subgroup_raw,
  CAST(NULLIF(ENROLLMENT,'s') AS INTEGER)             AS enrollment,
  CAST(NULLIF(ABSENT_COUNT,'s') AS INTEGER)           AS absent_count,
  CASE WHEN NULLIF(ABSENT_RATE,'s') IS NOT NULL
       THEN CAST(NULLIF(ABSENT_RATE,'s') AS REAL)/100.0 END AS absent_rate,
  DATA_REP_FLAG,
  PARTIAL_DATA_FLAG,
  COUNT_ZERO_NON_DISPLAY_FLAG
FROM acc_em_chronic_absenteeism
WHERE SUBJECT='38_CA';

-- ASSESSMENT (ELA + Math; percent -> proportion)
CREATE TEMP TABLE st_assessment_em_num AS
SELECT
  CAST(YEAR AS INTEGER)                                AS year_key,
  ENTITY_CD                                           AS school_id,
  INSTITUTION_ID                                      AS institution_id,
  TRIM(SUBGROUP_NAME)                                 AS subgroup_raw,
  'ELA'                                               AS subject,
  TRIM(GRADE)                                         AS grade,
  CAST(NULLIF(NUM_TESTED,'s') AS INTEGER)             AS tested,
  CAST(NULLIF(N_PROF,'s') AS INTEGER)                 AS n_qual,
  CASE WHEN NULLIF(PER_PROF,'s') IS NOT NULL
       THEN CAST(NULLIF(PER_PROF,'s') AS REAL)/100.0 END AS qual_rate
FROM annual_em_ela
WHERE GRADE IN ('3','4','5','6','7','8','All')
UNION ALL
SELECT
  CAST(YEAR AS INTEGER),
  ENTITY_CD,
  INSTITUTION_ID,
  TRIM(SUBGROUP_NAME),
  'Math',
  TRIM(GRADE),
  CAST(NULLIF(NUM_TESTED,'s') AS INTEGER),
  CAST(NULLIF(N_PROF,'s') AS INTEGER),
  CASE WHEN NULLIF(PER_PROF,'s') IS NOT NULL
       THEN CAST(NULLIF(PER_PROF,'s') AS REAL)/100.0 END
FROM annual_em_math
WHERE GRADE IN ('3','4','5','6','7','8','All');

-- ORG lookup
CREATE TEMP TABLE st_org AS
SELECT
  ENTITY_CD      AS school_id,
  SCHOOL_NAME    AS school_name,
  DISTRICT_CD    AS district_id,
  DISTRICT_NAME  AS district_name,
  COUNTY_NAME,
  NEEDS_INDEX,
  NEEDS_INDEX_DESCRIPTION
FROM boces_n_rc;

-- Subgroup mapping table (populated externally)
CREATE TABLE IF NOT EXISTS map_subgroups (
  raw_label TEXT PRIMARY KEY,
  subgroup_id TEXT,
  subgroup_name TEXT
);
