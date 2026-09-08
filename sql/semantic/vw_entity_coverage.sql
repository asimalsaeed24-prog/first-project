-- How far the CTI register actually covers what the reports talk about.
--
-- This is the breakdown that used to be pasted as an email into the bottom of
-- the dbt fact_report.sql. Computed from the model instead of typed by hand, so
-- it moves when the data moves.
--
-- One row per metric, which is the shape a BI tool wants for a tile or a bar.

SELECT
  'cti_entities' AS metric,
  count(*) AS value
FROM {{ target_schema }}.dim_entity
WHERE id <> -1
  AND is_cti_entity

UNION ALL

SELECT
  'cti_entities_with_prm_id',
  count(*)
FROM {{ target_schema }}.dim_entity
WHERE id <> -1
  AND is_cti_entity
  AND prm_id IS NOT NULL

UNION ALL

SELECT
  'label_only_entities',
  count(*)
FROM {{ target_schema }}.dim_entity
WHERE id <> -1
  AND NOT is_cti_entity

UNION ALL

-- Member slots on reports that resolved to nothing: the reports name an entity
-- the register does not have.
SELECT
  'unresolved_report_members',
  count(*)
FROM {{ target_schema }}.bridge_entity
WHERE is_unknown_member

UNION ALL

SELECT
  'reports_with_no_known_entity',
  count(DISTINCT report_id)
FROM {{ target_schema }}.vw_report_entity
WHERE is_unknown_member
