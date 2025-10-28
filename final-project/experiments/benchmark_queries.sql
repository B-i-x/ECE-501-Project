.headers on
.mode column
.timer on
-- If your sqlite3 supports it, uncomment the next line to show query plans inline.
-- .eqp on

/* =========================================================
   NYSED Benchmark Queries (Star Schema + Baseline stubs)
   Usage:
     sqlite3 db/nysed.sqlite < experiments/benchmark_queries.sql
   ========================================================= */

PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA cache_size = -800000;      -- ~800MB if RAM allows; adjust as needed
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;

/* ---------------------------------------------------------
   Q1 — Absence Rate vs. Proficiency (Year × School)
   Star schema
--------------------------------------------------------- */
-- EXPLAIN QUERY PLAN
-- SELECT ... (uncomment the next block to see plan)
-- EXPLAIN QUERY PLAN
SELECT
  y.year_key AS year,
  s.school_name,
  AVG(att.absence_rate) AS avg_absence_rate,
  AVG(ass.qual_rate)    AS avg_prof_rate
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key = ass.school_key
 AND att.year_key   = ass.year_key
JOIN dim_school s USING(school_key)
JOIN dim_year   y USING(year_key)
GROUP BY y.year_key, s.school_key
ORDER BY y.year_key, s.school_name;

/* ---------------------------------------------------------
   Q2 — Subgroup Comparison (Attendance × Achievement)
   Star schema
--------------------------------------------------------- */
-- EXPLAIN QUERY PLAN
SELECT
  y.year_key,
  sg.subgroup_name,
  AVG(att.absence_rate) AS avg_absence_rate,
  AVG(ass.qual_rate)    AS avg_prof_rate
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key   = ass.school_key
 AND att.year_key     = ass.year_key
 AND att.subgroup_key = ass.subgroup_key
JOIN dim_subgroup sg USING(subgroup_key)
JOIN dim_year     y  USING(year_key)
GROUP BY y.year_key, sg.subgroup_name
ORDER BY y.year_key, avg_absence_rate DESC;

/* ---------------------------------------------------------
   Q3 — Year-over-Year Change in Proficiency by District
   Star schema
--------------------------------------------------------- */
WITH prof AS (
  SELECT
    d.district_name,
    y.year_key,
    AVG(ass.qual_rate) AS avg_prof_rate
  FROM fact_assessment ass
  JOIN dim_school   s  USING(school_key)
  JOIN dim_district d  USING(district_key)
  JOIN dim_year     y  USING(year_key)
  WHERE ass.subject_key IN (
    SELECT subject_key FROM dim_subject WHERE subject_id IN ('ELA','Math')
  )
  GROUP BY d.district_name, y.year_key
)
SELECT
  p1.district_name,
  p2.year_key AS current_year,
  p2.avg_prof_rate - p1.avg_prof_rate AS delta_prof_rate
FROM prof p1
JOIN prof p2
  ON p1.district_name = p2.district_name
 AND p2.year_key = p1.year_key + 1
ORDER BY delta_prof_rate DESC;

/* ---------------------------------------------------------
   Q4 — Attendance Threshold and Achievement Distribution
   Star schema (ELA only)
--------------------------------------------------------- */
SELECT
  CASE
    WHEN att.absence_rate < 0.05 THEN 'Low Absence (<5%)'
    WHEN att.absence_rate < 0.10 THEN 'Moderate (5–10%)'
    ELSE 'High Absence (>10%)'
  END AS absence_band,
  ROUND(AVG(ass.qual_rate), 3) AS avg_prof_rate,
  COUNT(DISTINCT att.school_key) AS n_schools
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key   = ass.school_key
 AND att.year_key     = ass.year_key
 AND att.subgroup_key = ass.subgroup_key
WHERE ass.subject_key = (SELECT subject_key FROM dim_subject WHERE subject_id = 'ELA')
GROUP BY absence_band
ORDER BY avg_prof_rate DESC;

/* ---------------------------------------------------------
   Q5 — Top-Performing Schools by Chronic Absence (ELA)
   Star schema
--------------------------------------------------------- */
SELECT
  y.year_key,
  s.school_name,
  d.district_name,
  att.absence_rate,
  ass.qual_rate AS ela_prof_rate
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key = ass.school_key
 AND att.year_key   = ass.year_key
JOIN dim_school   s USING(school_key)
JOIN dim_district d USING(district_key)
JOIN dim_year     y USING(year_key)
WHERE ass.subject_key = (SELECT subject_key FROM dim_subject WHERE subject_id = 'ELA')
  AND att.absence_rate < 0.05
ORDER BY ass.qual_rate DESC
LIMIT 10;

/* =========================================================
   (Optional) Baseline stubs — fill with your baseline table names
   These are commented out so teammates can adapt locally.
========================================================= */
-- -- Baseline 1 (wide)
-- SELECT
--   year,
--   school_id,
--   AVG(absence_rate) AS avg_absence_rate,
--   AVG(ela_prof_rate) AS avg_ela_prof,
--   AVG(math_prof_rate) AS avg_math_prof
-- FROM wide_report_card
-- WHERE grade IN ('All', '3','4','5','6','7','8')
-- GROUP BY year, school_id;

-- -- Baseline 2 (normalized)
-- SELECT
--   a.year,
--   a.school_id,
--   AVG(a.absence_rate) AS avg_absence_rate,
--   AVG(p.qual_rate)    AS avg_prof_rate
-- FROM attendance a
-- JOIN performance p
--   ON a.school_id = p.school_id
--  AND a.year      = p.year
--  AND p.subject  IN ('ELA','Math')
-- GROUP BY a.year, a.school_id;

/* =========================================================
   Tips:
   - To capture timings into a CSV:
   -- .output figs/query_perf.txt
   -- (run queries)
   -- .output stdout
   - To see individual plans: prefix any SELECT with EXPLAIN QUERY PLAN
========================================================= */
