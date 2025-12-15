WITH base AS (
  SELECT
    math_prof_rate,
    per_ell, per_swd, per_ecdis, per_black, per_hisp, per_asian, per_white
  FROM pairs_year
  WHERE math_prof_rate IS NOT NULL
),
stats AS (
  SELECT
    COUNT(*) AS n,
    SUM(math_prof_rate) AS sumy,
    SUM(math_prof_rate * math_prof_rate) AS sumy2
  FROM base
),
s_ell AS (
  SELECT 'per_ell' AS var, COUNT(*) n,
         SUM(per_ell) sumx, SUM(per_ell*per_ell) sumx2,
         SUM(per_ell*math_prof_rate) sumxy
  FROM base WHERE per_ell IS NOT NULL
),
s_swd AS (
  SELECT 'per_swd', COUNT(*), SUM(per_swd), SUM(per_swd*per_swd), SUM(per_swd*math_prof_rate)
  FROM base WHERE per_swd IS NOT NULL
),
s_ecdis AS (
  SELECT 'per_ecdis', COUNT(*), SUM(per_ecdis), SUM(per_ecdis*per_ecdis), SUM(per_ecdis*math_prof_rate)
  FROM base WHERE per_ecdis IS NOT NULL
),
s_black AS (
  SELECT 'per_black', COUNT(*), SUM(per_black), SUM(per_black*per_black), SUM(per_black*math_prof_rate)
  FROM base WHERE per_black IS NOT NULL
),
s_hisp AS (
  SELECT 'per_hisp', COUNT(*), SUM(per_hisp), SUM(per_hisp*per_hisp), SUM(per_hisp*math_prof_rate)
  FROM base WHERE per_hisp IS NOT NULL
),
s_asian AS (
  SELECT 'per_asian', COUNT(*), SUM(per_asian), SUM(per_asian*per_asian), SUM(per_asian*math_prof_rate)
  FROM base WHERE per_asian IS NOT NULL
),
s_white AS (
  SELECT 'per_white', COUNT(*), SUM(per_white), SUM(per_white*per_white), SUM(per_white*math_prof_rate)
  FROM base WHERE per_white IS NOT NULL
),
allstats AS (
  SELECT * FROM s_ell
  UNION ALL SELECT * FROM s_swd
  UNION ALL SELECT * FROM s_ecdis
  UNION ALL SELECT * FROM s_black
  UNION ALL SELECT * FROM s_hisp
  UNION ALL SELECT * FROM s_asian
  UNION ALL SELECT * FROM s_white
)
SELECT
  a.var,
  a.n,
  CASE
    WHEN (a.n * a.sumx2 - a.sumx * a.sumx) <= 0
      OR (s.n * s.sumy2 - s.sumy * s.sumy) <= 0
      THEN NULL
    ELSE (a.n * a.sumxy - a.sumx * s.sumy)
         / sqrt( (a.n * a.sumx2 - a.sumx * a.sumx)
               * (s.n * s.sumy2 - s.sumy * s.sumy) )
  END AS r,
  CASE
    WHEN (a.n * a.sumx2 - a.sumx * a.sumx) = 0
      THEN NULL
    ELSE (a.n * a.sumxy - a.sumx * s.sumy)
         / (a.n * a.sumx2 - a.sumx * a.sumx)
  END AS slope
FROM allstats a
CROSS JOIN stats s
ORDER BY ABS(r) DESC;
