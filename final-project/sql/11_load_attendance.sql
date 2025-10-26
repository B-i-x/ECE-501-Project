/* fact_attendance: chronic absenteeism (proportion) */
INSERT OR REPLACE INTO fact_attendance(
  year_key, school_key, subgroup_key, absent_count, absence_rate, enrollment,
  data_rep_flag, partial_data_flag, count_zero_flag
)
SELECT
  y.year_key,
  s.school_key,
  g.subgroup_key,
  a.absent_count,
  a.absent_rate,
  a.enrollment,
  a.DATA_REP_FLAG,
  a.PARTIAL_DATA_FLAG,
  a.COUNT_ZERO_NON_DISPLAY_FLAG
FROM st_attendance_em_num a
JOIN dim_year y     ON y.year_key = a.year_key
JOIN dim_school s   ON s.school_id = a.school_id
LEFT JOIN map_subgroups m ON m.raw_label = a.subgroup_raw
JOIN dim_subgroup g ON g.subgroup_id = COALESCE(m.subgroup_id, a.subgroup_raw);
