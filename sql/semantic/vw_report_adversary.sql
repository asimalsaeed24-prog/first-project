SELECT
  r.report_id,
  r.title,
  r.report_date,
  r.classification,
  r.importance,
  r.threat_type,

  d.id AS adversary_id,
  d.adversary_name,

  b.weight_factor,
  b.is_unknown_member

FROM {{ target_schema }}.vw_report r

JOIN {{ target_schema }}.bridge_adversary b
  ON r.adversary_group_key = b.adversary_group_key

JOIN {{ target_schema }}.dim_cti_adversary d
  ON b.adversary_dim_id = d.id