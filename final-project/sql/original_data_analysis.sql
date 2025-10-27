ATTACH 'C:/Users/alexr/Documents/Fall 2025/ECE 501/ECE-501-Project/data/sqlite/src2024.db' AS src;

WITH math AS (
  SELECT
    ENTITY_CD,
    CAST(YEAR AS INTEGER) AS year,
    SUBGROUP_NAME,
    SUM(CAST(NUM_TESTED AS INTEGER)) AS num_tested,
    SUM(CAST(NUM_PROF  AS INTEGER)) AS num_prof
  FROM src."Annual EM MATH"
  WHERE ASSESSMENT_NAME LIKE 'Grade %'
  GROUP BY ENTITY_CD, CAST(YEAR AS INTEGER), SUBGROUP_NAME
),
tot AS (
  SELECT ENTITY_CD, year, SUM(num_tested) AS total_tested
  FROM math
  GROUP BY ENTITY_CD, year
),
pairs AS (
  SELECT
    m.ENTITY_CD,
    m.year,
    m.SUBGROUP_NAME,
    CASE WHEN t.total_tested > 0 THEN 1.0 * m.num_tested / t.total_tested ELSE NULL END AS sg_share,
    CASE WHEN m.num_tested > 0 THEN 1.0 * m.num_prof / m.num_tested ELSE NULL END AS sg_prof
  FROM math m
  JOIN tot t ON t.ENTITY_CD = m.ENTITY_CD AND t.year = m.year
  WHERE m.SUBGROUP_NAME NOT IN ('All Students')
),
corr_per_school_year AS (
  SELECT
    ENTITY_CD,
    year,
    COUNT(*) AS n,
    SUM(sg_share) AS sumx,
    SUM(sg_prof)  AS sumy,
    SUM(sg_share * sg_prof) AS sumxy,
    SUM(sg_share * sg_share) AS sumx2,
    SUM(sg_prof * sg_prof)   AS sumy2
  FROM pairs
  WHERE sg_share IS NOT NULL AND sg_prof IS NOT NULL
  GROUP BY ENTITY_CD, year
)
SELECT
  c.ENTITY_CD,
  c.year,
  CASE
    WHEN (c.n * c.sumx2 - c.sumx * c.sumx) <= 0
      OR (c.n * c.sumy2 - c.sumy * c.sumy) <= 0
      THEN NULL
    ELSE (c.n * c.sumxy - c.sumx * c.sumy)
         / SQRT( (c.n * c.sumx2 - c.sumx * c.sumx)
               * (c.n * c.sumy2 - c.sumy * c.sumy) )
  END AS r_share_vs_prof_within_school_year
FROM corr_per_school_year c
ORDER BY c.ENTITY_CD, c.year;
