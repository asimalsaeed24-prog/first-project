SELECT
  r.report_id,
  r.title,
  r.report_date,
  r.classification,
  r.importance,
  r.threat_type,

  e.id AS entity_id,
  e.entity_name_en,
  e.entity_name_ar,
  e.cti_id,
  e.prm_id,
  e.sector,
  e.category,
  e.entity_type,
  e.country AS entity_country,
  e.is_cti_entity,

  b.weight_factor,
  b.is_unknown_member

FROM {{ target_schema }}.vw_report r

JOIN {{ target_schema }}.bridge_entity b
  ON r.entity_group_key = b.entity_group_key

JOIN {{ target_schema }}.dim_rasd_entity e
  ON b.entity_id = e.id
