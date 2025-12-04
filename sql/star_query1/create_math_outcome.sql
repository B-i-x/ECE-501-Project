CREATE TEMP VIEW math_outcome AS
SELECT
  entity_cd,
  year,
  CASE WHEN num_tested > 0 THEN 1.0 * num_prof / num_tested END AS math_prof_rate
FROM math_overall;
