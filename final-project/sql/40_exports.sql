-- Example CSV exports (run with: sqlite3 -header -csv db/nysed.sqlite < sql/40_exports.sql > figs/abs_vs_prof.csv)

-- Absence vs ELA/Math proficiency, by subgroup
SELECT
  year,
  district_name,
  school_name,
  subgroup_id,
  ROUND(absence_rate,4) AS absence_rate,
  ROUND(ela_qual_rate,4) AS ela_qual_rate,
  ROUND(math_qual_rate,4) AS math_qual_rate
FROM v_absence_vs_proficiency
ORDER BY year, district_name, school_name, subgroup_id;

-- District-level subgroup gaps (F - M) in ELA
WITH by_group AS (
  SELECT year, district_name, subgroup_id, AVG(ela_qual_rate) AS ela_rate
  FROM v_absence_vs_proficiency
  GROUP BY year, district_name, subgroup_id
),
female AS (SELECT year, district_name, ela_rate FROM by_group WHERE subgroup_id='F'),
male   AS (SELECT year, district_name, ela_rate FROM by_group WHERE subgroup_id='M')
SELECT f.year, f.district_name, ROUND(f.ela_rate - m.ela_rate,4) AS ela_gap_F_minus_M
FROM female f JOIN male m
  ON m.year=f.year AND m.district_name=f.district_name
ORDER BY f.year, f.district_name;
