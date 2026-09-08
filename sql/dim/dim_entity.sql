SELECT
  CAST(-1 AS BIGINT) AS id,
  CAST(NULL AS STRING) AS cti_id,
  CAST(NULL AS STRING) AS prm_id,
  'Unknown' AS entity_name_en,
  'غير معروف' AS entity_name_ar,
  CAST(NULL AS STRING) AS country,
  CAST(NULL AS STRING) AS category,
  CAST(NULL AS STRING) AS sector,
  CAST(NULL AS STRING) AS entity_type,
  CAST(NULL AS STRING) AS domain,
  false AS is_cti_entity

UNION ALL

SELECT
  k.id,
  e.cti_id,
  e.prm_id,
  coalesce(e.entity_name_en, k.label) AS entity_name_en,
  coalesce(e.entity_name_ar, k.label) AS entity_name_ar,
  e.country,
  e.category,
  e.sector,
  e.entity_type,
  e.domain,
  coalesce(e.is_cti_entity, false) AS is_cti_entity
FROM {{ target_schema }}.dim_key k
LEFT JOIN {{ target_schema }}.stg_entity e
  ON e.entity_natural_key = k.natural_key
WHERE k.dimension = 'dim_entity'
