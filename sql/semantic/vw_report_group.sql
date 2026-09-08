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
