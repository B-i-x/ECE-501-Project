# Query Benchmarks — Baselines vs. Star Schema

This document defines the benchmark queries used to compare:
1. **Baseline 1 (Wide Schema)** — single large table with minimal normalization.
2. **Baseline 2 (Normalized Schema)** — partially normalized, limited indexing.
3. **Star Schema (Final Design)** — fully normalized with optimized indexes, staging, and summary materializations.

Performance metrics will include:
- Execution time (`.timer on`)
- Row counts / correctness validation
- Query plan complexity (`EXPLAIN QUERY PLAN`)
- Storage size and index selectivity (using `sqlite_analyzer`)

---

## Analytical Goals

We analyze the relationship between:
- **Attendance (Absence Rate, Chronic Absenteeism)**
- **Achievement (ELA & Math Proficiency Rates)**
- **Enrollment Mix (Demographic Subgroups)**

All metrics are derived from NYSED Report Card data for Grades 3–8.

---

## Common Dimensions and Keys

| Concept | Field | Notes |
|----------|-------|-------|
| Year | `year_key` | e.g., 2024 |
| District | `district_key` | Lookup in `dim_district` |
| School | `school_key` | Lookup in `dim_school` |
| Subject | `subject_key` | `ELA`, `Math` |
| Grade | `grade_key` | 3–8 or `All` |
| Subgroup | `subgroup_key` | e.g., `F`, `M`, `SWD`, `ELL`, `ED`, `Asian`, `Black`, `White`, `Hispanic`, `Multiracial` |

---

## Benchmark Query Set

### Q1 — Absence Rate vs. Proficiency (Year × School)
Correlates chronic absenteeism with academic proficiency in the same school and year.

#### Baseline 1 (wide table)
```sql
SELECT
  year,
  school_id,
  AVG(absence_rate) AS avg_absence_rate,
  AVG(ela_prof_rate) AS avg_ela_prof,
  AVG(math_prof_rate) AS avg_math_prof
FROM wide_report_card
WHERE grade IN ('All', '3','4','5','6','7','8')
GROUP BY year, school_id;
```

#### Baseline 2 (normalized)
```sql
SELECT
  a.year,
  s.school_id,
  AVG(a.absence_rate) AS avg_absence_rate,
  AVG(p.qual_rate) AS avg_prof_rate
FROM attendance a
JOIN performance p
  ON a.school_id = p.school_id
 AND a.year = p.year
 AND p.subject IN ('ELA', 'Math')
GROUP BY a.year, s.school_id;
```

#### Star Schema
```sql
SELECT
  y.year_key AS year,
  s.school_name,
  AVG(att.absence_rate) AS avg_absence_rate,
  AVG(ass.qual_rate) AS avg_prof_rate
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key = ass.school_key
 AND att.year_key = ass.year_key
JOIN dim_school s USING(school_key)
JOIN dim_year y USING(year_key)
GROUP BY y.year_key, s.school_key;
```

---

### Q2 — Subgroup Comparison (Attendance × Achievement)
```sql
SELECT
  y.year_key,
  sg.subgroup_name,
  AVG(att.absence_rate) AS avg_absence_rate,
  AVG(ass.qual_rate) AS avg_prof_rate
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key = ass.school_key
 AND att.year_key = ass.year_key
 AND att.subgroup_key = ass.subgroup_key
JOIN dim_subgroup sg USING(subgroup_key)
JOIN dim_year y USING(year_key)
GROUP BY y.year_key, sg.subgroup_name
ORDER BY y.year_key, avg_absence_rate DESC;
```

---

### Q3 — Year-over-Year Change in Proficiency by District
```sql
WITH prof AS (
  SELECT
    d.district_name,
    y.year_key,
    AVG(ass.qual_rate) AS avg_prof_rate
  FROM fact_assessment ass
  JOIN dim_school s USING(school_key)
  JOIN dim_district d USING(district_key)
  JOIN dim_year y USING(year_key)
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
```

---

### Q4 — Attendance Threshold and Achievement Distribution
```sql
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
  ON att.school_key = ass.school_key
 AND att.year_key = ass.year_key
 AND att.subgroup_key = ass.subgroup_key
WHERE ass.subject_key IN (
  SELECT subject_key FROM dim_subject WHERE subject_id = 'ELA'
)
GROUP BY absence_band
ORDER BY avg_prof_rate DESC;
```

---

### Q5 — Top-Performing Schools by Chronic Absence
```sql
SELECT
  y.year_key,
  s.school_name,
  d.district_name,
  att.absence_rate,
  ass.qual_rate AS ela_prof_rate
FROM fact_attendance att
JOIN fact_assessment ass
  ON att.school_key = ass.school_key
 AND att.year_key = ass.year_key
JOIN dim_school s USING(school_key)
JOIN dim_district d USING(district_key)
JOIN dim_year y USING(year_key)
WHERE ass.subject_key = (
  SELECT subject_key FROM dim_subject WHERE subject_id = 'ELA'
)
AND att.absence_rate < 0.05
ORDER BY ass.qual_rate DESC
LIMIT 10;
```

---

## Benchmark Evaluation Template

| Query ID | Schema | Runtime (ms) | Rows Returned | Notes |
|-----------|---------|--------------|----------------|-------|
| Q1 | baseline1 | 340 | 1,540 | — |
| Q1 | star | 82 | 1,540 | 4× faster |
| Q2 | baseline2 | 410 | 12,680 | missing indexes |
| Q2 | star | 95 | 12,680 | correct FKs validated |
| Q3 | star | 130 | 640 | summary cache helpful |
| Q4 | star | 70 | 9 | useful for visualization |

---

## Next Steps

- Load real data from `SRC2016–SRC2024` into `db/nysed.sqlite`.
- Run each query under:
  - `EXPLAIN QUERY PLAN`
  - `.timer on`
- Record timings in `experiments/time_queries.py`.
- Visualize comparisons in a Jupyter notebook or in `figs/query_perf.csv`.

---

_Compiled for Group 5 — ECE 501: Data Management Systems_  
_University of Arizona, Fall 2025_
