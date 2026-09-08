-- One row per report per country. A report naming three countries appears three
-- times, so COUNT(*) over this view counts mentions, not reports.
--
-- To count reports without double counting, sum weight_factor instead: a report
-- spread over three countries contributes 1/3 to each, and they add back up to 1.
--
--     SELECT country_name, sum(weight_factor) AS reports
--     FROM {{ target_schema }}.vw_report_country
--     GROUP BY country_name
--
-- is_unknown_member marks a member that could not be resolved to a real
-- country -- either the report named none, or it named one the warehouse has
-- never seen.

SELECT
  r.report_id,
  r.title,
  r.report_date,
  r.classification,
  r.importance,
  r.threat_type,

  d.id AS country_id,
  d.country_name,

  b.weight_factor,
  b.is_unknown_member

FROM {{ target_schema }}.vw_report r

JOIN {{ target_schema }}.bridge_country b
  ON r.country_group_key = b.country_group_key

JOIN {{ target_schema }}.dim_country d
  ON b.country_id = d.id
