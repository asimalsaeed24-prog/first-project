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
