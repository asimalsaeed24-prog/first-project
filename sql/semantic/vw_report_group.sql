-- One row per report per threat group. A report naming three threat groups appears three
-- times, so COUNT(*) over this view counts mentions, not reports.
--
-- To count reports without double counting, sum weight_factor instead: a report
-- spread over three threat groups contributes 1/3 to each, and they add back up to 1.
--
--     SELECT group_name, sum(weight_factor) AS reports
--     FROM {{ target_schema }}.vw_report_group
--     GROUP BY group_name
--
-- is_unknown_member marks a member that could not be resolved to a real
-- threat group -- either the report named none, or it named one the warehouse has
-- never seen.

SELECT
  r.report_id,
  r.title,
  r.report_date,
  r.classification,
  r.importance,
  r.threat_type,

  d.id AS group_id,
  d.group_name,

  b.weight_factor,
  b.is_unknown_member

FROM {{ target_schema }}.vw_report r

JOIN {{ target_schema }}.bridge_group b
  ON r.group_group_key = b.group_group_key

JOIN {{ target_schema }}.dim_group d
  ON b.group_id = d.id
