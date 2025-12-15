/* fact_expenditures: per-pupil expenditure by (year, school) */
INSERT OR IGNORE INTO dim_year(year_key)
SELECT DISTINCT year_key FROM st_years;

-- fact_expenditures from expenditures staging
INSERT OR REPLACE INTO fact_expenditures(
  year_key, school_key, per_pupil_expenditure, data_reported_exp, data_reported_enr
)
SELECT
  y.year_key,
  s.school_key,
  e.per_pupil_expenditure,
  e.DATA_REPORTED_EXP,
  e.DATA_REPORTED_ENR
FROM st_expenditures e
JOIN dim_year y     ON y.year_key = e.year_key
JOIN dim_school s   ON s.school_id = e.school_id;

