/* fact_enrollment: derive enrollment by (year, school, subgroup) from attendance staging */
INSERT OR IGNORE INTO dim_year(year_key)
SELECT DISTINCT year_key FROM st_years;

-- seed districts & schools (by natural IDs) if not already there
INSERT OR IGNORE INTO dim_district(district_id, district_name, county_name, nrc_code, nrc_desc)
SELECT DISTINCT district_id, district_name, county_name, needs_index, needs_index_description
FROM st_org WHERE district_id IS NOT NULL;

INSERT OR IGNORE INTO dim_school(school_id, school_name, district_key)
SELECT o.school_id, o.school_name, d.district_key
FROM st_org o
JOIN dim_district d ON d.district_id = o.district_id
WHERE o.school_id IS NOT NULL
ON CONFLICT(school_id) DO NOTHING;

-- Seed subgroups from observed labels (fallback if map_subgroups not populated)
INSERT OR IGNORE INTO dim_subgroup(subgroup_id, subgroup_name)
SELECT DISTINCT COALESCE(m.subgroup_id, r.subgroup_raw),
       COALESCE(m.subgroup_name, r.subgroup_raw)
FROM (SELECT DISTINCT subgroup_raw FROM st_attendance_em_num) r
LEFT JOIN map_subgroups m ON m.raw_label = r.subgroup_raw;

-- fact_enrollment from attendance staging
INSERT OR REPLACE INTO fact_enrollment(year_key, school_key, subgroup_key, n_students)
SELECT
  y.year_key,
  s.school_key,
  g.subgroup_key,
  a.enrollment
FROM st_attendance_em_num a
JOIN dim_year y     ON y.year_key = a.year_key
JOIN dim_school s   ON s.school_id = a.school_id
LEFT JOIN map_subgroups m ON m.raw_label = a.subgroup_raw
JOIN dim_subgroup g ON g.subgroup_id = COALESCE(m.subgroup_id, a.subgroup_raw);
