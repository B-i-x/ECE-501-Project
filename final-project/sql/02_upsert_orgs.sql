-- From st_org (built in 09_staging.sql) → dim_district, dim_school

INSERT OR IGNORE INTO dim_district(district_id, district_name, county_name, nrc_code, nrc_desc)
SELECT DISTINCT district_id, district_name, county_name, needs_index, needs_index_description
FROM st_org
WHERE district_id IS NOT NULL;

INSERT OR IGNORE INTO dim_school(school_id, school_name, district_key)
SELECT o.school_id, o.school_name, d.district_key
FROM st_org o
JOIN dim_district d ON d.district_id = o.district_id
WHERE o.school_id IS NOT NULL;
