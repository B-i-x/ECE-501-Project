-- Query 2: Attendance vs Math Proficiency (Star Schema Version)
-- Within 2024, across all schools, how does school-level attendance rate relate to math proficiency rates?

WITH math_school AS (
    SELECT
        s.school_id AS ENTITY_CD,
        y.year_key AS YEAR,
        AVG(fa.qual_rate) * 100.0 AS math_prof_rate
    FROM fact_assessment fa
    JOIN dim_school s ON s.school_key = fa.school_key
    JOIN dim_year y ON y.year_key = fa.year_key
    JOIN dim_subject subj ON subj.subject_key = fa.subject_key
    JOIN dim_subgroup sg ON sg.subgroup_key = fa.subgroup_key
    WHERE y.year_key = 2024
      AND subj.subject_id = 'Math'
      AND UPPER(TRIM(sg.subgroup_name)) LIKE 'ALL STUDENTS%'
    GROUP BY s.school_id, y.year_key
),
att_school AS (
    SELECT
        s.school_id AS ENTITY_CD,
        s.school_name AS ENTITY_NAME,
        y.year_key AS YEAR,
        (1.0 - AVG(fa.absence_rate)) * 100.0 AS ATTENDANCE_RATE  -- Convert absence_rate (0-1) to attendance_rate percentage
    FROM fact_attendance fa
    JOIN dim_school s ON s.school_key = fa.school_key
    JOIN dim_year y ON y.year_key = fa.year_key
    JOIN dim_subgroup sg ON sg.subgroup_key = fa.subgroup_key
    WHERE y.year_key = 2024
      AND UPPER(TRIM(sg.subgroup_name)) LIKE 'ALL STUDENTS%'
    GROUP BY s.school_id, s.school_name, y.year_key
)
SELECT
    a.ENTITY_CD,
    a.ENTITY_NAME,
    a.ATTENDANCE_RATE,
    m.math_prof_rate
FROM att_school AS a
JOIN math_school AS m
  ON a.ENTITY_CD = m.ENTITY_CD
 AND a.YEAR = m.YEAR
WHERE a.ENTITY_NAME NOT LIKE '% SD'
  AND m.math_prof_rate IS NOT NULL
  AND m.math_prof_rate > 0
  AND a.ATTENDANCE_RATE IS NOT NULL
  AND a.ATTENDANCE_RATE >= 0;

