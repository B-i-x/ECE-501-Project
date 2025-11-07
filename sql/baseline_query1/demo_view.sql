DROP VIEW IF EXISTS demo;
CREATE TEMP VIEW demo AS
SELECT
  d.ENTITY_CD AS entity_cd,
  CAST(d.YEAR AS INTEGER) AS year,
  CAST(d.PER_ELL   AS REAL) AS per_ell,
  CAST(d.PER_SWD   AS REAL) AS per_swd,
  CAST(d.PER_ECDIS AS REAL) AS per_ecdis,
  CAST(d.PER_BLACK AS REAL) AS per_black,
  CAST(d.PER_HISP  AS REAL) AS per_hisp,
  CAST(d.PER_ASIAN AS REAL) AS per_asian,
  CAST(d.PER_WHITE AS REAL) AS per_white
FROM enr."Demographic Factors" d;
