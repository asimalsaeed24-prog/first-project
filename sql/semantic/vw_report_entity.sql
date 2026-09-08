-- One row per report per entity. A report naming three entities appears three
-- times, so COUNT(*) over this view counts mentions, not reports.
--
-- To count reports without double counting, sum weight_factor instead: a report
-- spread over three entities contributes 1/3 to each, and they add back up to 1.
--
--     SELECT sector, sum(weight_factor) AS reports
--     FROM {{ target_schema }}.vw_report_entity
--     GROUP BY sector
--
-- is_unknown_member marks a member that did not resolve to a known entity.
-- That is mostly the "RASD id on the report but no CTI id" cohort -- those
-- reports name an entity the CTI register has never heard of. Filter it out
-- when you only want registered entities, or group by it to size the gap.

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

JOIN {{ target_schema }}.dim_entity e
  ON b.entity_id = e.id
