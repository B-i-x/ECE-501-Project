/* Cleanup script to drop all staging tables safely.
   Run this before re-running 09_staging_persistent.sql
   if you want to rebuild from scratch.
*/

PRAGMA foreign_keys=OFF;

DROP TABLE IF EXISTS st_years;
DROP TABLE IF EXISTS st_attendance_em_num;
DROP TABLE IF EXISTS st_assessment_em_num;
DROP TABLE IF EXISTS st_org;
DROP TABLE IF EXISTS map_subgroups;

PRAGMA foreign_keys=ON;

SELECT 'Staging tables dropped. You can now run: make staging' AS message;
