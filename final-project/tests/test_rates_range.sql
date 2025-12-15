SELECT 'bad absence_rate', COUNT(*) FROM fact_attendance WHERE absence_rate<0 OR absence_rate>1;
SELECT 'bad qual_rate', COUNT(*) FROM fact_assessment WHERE qual_rate<0 OR qual_rate>1;
