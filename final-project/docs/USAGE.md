# Using the Star Schema and Summary Views

This guide explains how to query the NYSED star schema database and use the summary views for analysis.

## Quick Start

```bash
# Connect to the database
sqlite3 db/nysed.sqlite

# View available tables and views
.tables

# View summary data
SELECT * FROM v_summary_complete LIMIT 10;
```

## Available Views

### `v_summary_complete` — Main Summary View
**Best for**: Most common queries combining enrollment, attendance, and proficiency

**Columns**:
- `year`, `school_year_label` — Reporting year
- `district_id`, `district_name`, `county_name` — District information
- `school_id`, `school_name` — School information
- `subgroup_id`, `subgroup_name` — Demographic subgroup
- `n_students` — Enrollment count
- `absence_rate` — Absence rate (0-1 proportion)
- `absence_rate_pct` — Absence rate (0-100 percentage)
- `ela_qual_rate`, `ela_qual_rate_pct` — ELA proficiency (proportion and percentage)
- `math_qual_rate`, `math_qual_rate_pct` — Math proficiency (proportion and percentage)

### `v_absence_vs_proficiency` — Attendance vs. Proficiency
**Best for**: Analyzing the relationship between attendance and academic performance

**Columns**:
- `year`, `district_name`, `school_name`, `subgroup_id`
- `absence_rate`, `ela_qual_rate`, `math_qual_rate`

### `v_assessment_school_year` — Detailed Assessment Data
**Best for**: Subject and grade-level analysis

**Columns**:
- `year`, `school_key`, `school_name`, `district_key`, `district_name`
- `subject_id`, `grade_id`
- `subgroup_id`, `subgroup_name`
- `tested`, `n_qual`, `qual_rate`

## Example Queries

### 1. Find Schools with High Absence Rates

```sql
SELECT 
    school_name,
    district_name,
    absence_rate_pct,
    ela_qual_rate_pct,
    math_qual_rate_pct,
    n_students
FROM v_summary_complete
WHERE absence_rate_pct > 20
ORDER BY absence_rate_pct DESC
LIMIT 20;
```

### 2. Compare Subgroups Within a District

```sql
SELECT 
    subgroup_name,
    COUNT(DISTINCT school_id) AS num_schools,
    AVG(absence_rate_pct) AS avg_absence_pct,
    AVG(ela_qual_rate_pct) AS avg_ela_pct,
    AVG(math_qual_rate_pct) AS avg_math_pct,
    SUM(n_students) AS total_students
FROM v_summary_complete
WHERE district_name = 'ALBANY CITY SD'
GROUP BY subgroup_name
ORDER BY avg_absence_pct DESC;
```

### 3. Year-over-Year Trends

```sql
SELECT 
    year,
    COUNT(DISTINCT school_id) AS num_schools,
    SUM(n_students) AS total_students,
    AVG(absence_rate_pct) AS avg_absence_pct,
    AVG(ela_qual_rate_pct) AS avg_ela_pct,
    AVG(math_qual_rate_pct) AS avg_math_pct
FROM v_summary_complete
GROUP BY year
ORDER BY year;
```

### 4. Schools with Low Proficiency but Good Attendance

```sql
SELECT 
    school_name,
    district_name,
    absence_rate_pct,
    ela_qual_rate_pct,
    math_qual_rate_pct
FROM v_summary_complete
WHERE subgroup_id = 'All'
  AND absence_rate_pct < 10
  AND (ela_qual_rate_pct < 50 OR math_qual_rate_pct < 50)
ORDER BY absence_rate_pct;
```

### 5. District-Level Summary

```sql
SELECT 
    district_name,
    county_name,
    COUNT(DISTINCT school_id) AS num_schools,
    SUM(n_students) AS total_students,
    AVG(absence_rate_pct) AS avg_absence_pct,
    AVG(ela_qual_rate_pct) AS avg_ela_pct,
    AVG(math_qual_rate_pct) AS avg_math_pct
FROM v_summary_complete
WHERE subgroup_id = 'All'
GROUP BY district_name, county_name
HAVING total_students > 1000
ORDER BY avg_absence_pct DESC;
```

### 6. Subgroup Performance Comparison

```sql
SELECT 
    subgroup_name,
    COUNT(*) AS num_records,
    AVG(absence_rate_pct) AS avg_absence,
    AVG(ela_qual_rate_pct) AS avg_ela,
    AVG(math_qual_rate_pct) AS avg_math
FROM v_summary_complete
GROUP BY subgroup_name
ORDER BY avg_absence DESC;
```

### 7. Correlation: Absence Rate vs. Proficiency

```sql
SELECT 
    CASE 
        WHEN absence_rate_pct < 5 THEN 'Very Low (<5%)'
        WHEN absence_rate_pct < 10 THEN 'Low (5-10%)'
        WHEN absence_rate_pct < 20 THEN 'Moderate (10-20%)'
        WHEN absence_rate_pct < 30 THEN 'High (20-30%)'
        ELSE 'Very High (>30%)'
    END AS absence_category,
    COUNT(*) AS num_schools,
    AVG(ela_qual_rate_pct) AS avg_ela_pct,
    AVG(math_qual_rate_pct) AS avg_math_pct
FROM v_summary_complete
WHERE subgroup_id = 'All'
GROUP BY absence_category
ORDER BY absence_rate_pct;
```

### 8. Export Data for Analysis

```bash
# Export summary to CSV
sqlite3 -header -csv db/nysed.sqlite \
  "SELECT * FROM v_summary_complete WHERE year = 2023" \
  > summary_2023.csv

# Export specific query
sqlite3 -header -csv db/nysed.sqlite \
  "SELECT district_name, school_name, absence_rate_pct, ela_qual_rate_pct 
   FROM v_summary_complete 
   WHERE subgroup_id = 'All'" \
  > attendance_vs_ela.csv
```

## Querying the Star Schema Directly

For more complex queries, you can join the fact and dimension tables directly:

### Example: Detailed Assessment Analysis

```sql
SELECT 
    y.year_key,
    d.district_name,
    s.school_name,
    subj.subject_name,
    g.grade_id,
    sg.subgroup_name,
    fa.tested,
    fa.n_qual,
    fa.qual_rate
FROM fact_assessment fa
JOIN dim_year y ON y.year_key = fa.year_key
JOIN dim_school s ON s.school_key = fa.school_key
JOIN dim_district d ON d.district_key = s.district_key
JOIN dim_subject subj ON subj.subject_key = fa.subject_key
JOIN dim_grade g ON g.grade_key = fa.grade_key
JOIN dim_subgroup sg ON sg.subgroup_key = fa.subgroup_key
WHERE y.year_key = 2023
  AND subj.subject_id = 'ELA'
  AND sg.subgroup_id = 'All'
ORDER BY fa.qual_rate DESC
LIMIT 20;
```

### Example: Enrollment Trends

```sql
SELECT 
    y.year_key,
    d.district_name,
    sg.subgroup_name,
    SUM(fe.n_students) AS total_enrollment
FROM fact_enrollment fe
JOIN dim_year y ON y.year_key = fe.year_key
JOIN dim_school s ON s.school_key = fe.school_key
JOIN dim_district d ON d.district_key = s.district_key
JOIN dim_subgroup sg ON sg.subgroup_key = fe.subgroup_key
GROUP BY y.year_key, d.district_name, sg.subgroup_name
ORDER BY y.year_key, total_enrollment DESC;
```

## Refreshing the Summary Table

If you've updated the fact tables, refresh the summary:

```bash
# Refresh summary table
sqlite3 db/nysed.sqlite < sql/20_refresh_summary.sql

# Or rebuild everything
python etl/run_sql.py
```

### Measuring Refresh Performance

To measure how long it takes to refresh the summary table:

```bash
# Single run
python scripts/time_summary_refresh.py

# Multiple runs for statistics (P50, P95, etc.)
python scripts/time_summary_refresh.py --runs 10

# With custom warmup runs
python scripts/time_summary_refresh.py --runs 5 --warmup 2

# Save results to specific file
python scripts/time_summary_refresh.py --runs 10 --output my_timings.csv
```

Or using Make:
```bash
make time-summary
```

Results are automatically saved to `experiments/results/summary_refresh_timings_YYYYMMDD_HHMMSS.csv` when running multiple times.

## Common SQLite Commands

```sql
-- Set output format
.mode column
.headers on

-- Show table structure
.schema v_summary_complete

-- Count rows
SELECT COUNT(*) FROM v_summary_complete;

-- Show distinct values
SELECT DISTINCT subgroup_name FROM v_summary_complete;

-- Export query results
.mode csv
.headers on
.output results.csv
SELECT * FROM v_summary_complete LIMIT 100;
.output stdout
```

## Tips

1. **Use the views**: The `v_summary_complete` view is usually the easiest starting point
2. **Filter by subgroup**: Most analyses should filter `subgroup_id = 'All'` for school-level data, or compare specific subgroups
3. **Check for NULLs**: Some schools may have NULL values for certain metrics
4. **Use percentages**: The `*_pct` columns are easier to interpret than proportions
5. **Group appropriately**: Aggregate by district, school, year, or subgroup depending on your analysis

## Data Dictionary

See [`docs/data_dictionary.md`](data_dictionary.md) for complete table and column descriptions.

## Performance Notes

- The summary table (`fact_summary_sys`) is pre-computed for fast queries
- Views are virtual and don't store data (they're just saved queries)
- For large exports, consider using `.mode csv` and redirecting output
- Indexes are already created on key columns for performance

