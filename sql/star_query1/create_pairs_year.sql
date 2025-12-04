-- create_pairs_year.sql

CREATE TEMP VIEW pairs_year AS
SELECT
  o.entity_cd,
  o.year,
  o.math_prof_rate,
  d.per_ell,
  d.per_swd,
  d.per_ecdis,
  d.per_black,
  d.per_hisp,
  d.per_asian,
  d.per_white
FROM math_outcome o
JOIN demo d
  ON d.entity_cd = o.entity_cd AND d.year = o.year
WHERE o.year = (SELECT MAX(year) FROM math_outcome)
  AND o.math_prof_rate IS NOT NULL
  AND o.math_prof_rate > 0;