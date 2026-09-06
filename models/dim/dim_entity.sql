{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

-- This dimension table consolidates entity information from CTI/RASD sources
-- It includes both CTI entities and non-CTI entities with proper deduplication

WITH cti_entities AS (
  SELECT 
    cti_id AS id,
    client_name_en AS entity_name_en,
    client_name_ar AS entity_name_ar,
    country,
    category,
    sector,
    type_of_entity AS entity_type,
    "domain",
    true AS is_cti_entity,
    prm_id
  FROM {{ source('cti', 'entities') }}
  WHERE cti_id IS NOT NULL
),

none_cti_entities AS (
  SELECT DISTINCT
    split_name AS entity_name_ar,
    split_name AS entity_name_en
  FROM {{ source('cti', 'rasd') }}
  CROSS JOIN UNNEST(
    split(COALESCE(entities_names_ar, ''), '|')
  ) AS t(split_name)
  WHERE entities_cti_id IS NULL
    AND entities_names_ar IS NOT NULL
    AND split_name <> ''
    AND split_name IS NOT NULL
),

-- Combine both CTI and non-CTI entities
all_entities AS (
  -- Unknown entity placeholder
  SELECT
    -1 AS id,
    'Unknown' AS entity_name_en,
    'غير معروف' AS entity_name_ar,
    NULL AS cti_id,
    NULL AS prm_id,
    NULL AS country,
    NULL AS category,
    NULL AS sector,
    NULL AS entity_type,
    NULL AS domain,
    FALSE AS is_cti_entity

  UNION ALL

  -- CTI Entities
  SELECT
    entity_name_en,
    entity_name_ar,
    id AS cti_id,
    prm_id,
    country,
    category,
    sector,
    entity_type,
    domain,
    is_cti_entity
  FROM cti_entities

  UNION ALL

  -- Non-CTI Entities (deduplicated)
  SELECT
    entity_name_en,
    entity_name_ar,
    NULL AS cti_id,
    NULL AS prm_id,
    NULL AS country,
    NULL AS category,
    NULL AS sector,
    NULL AS entity_type,
    NULL AS domain,
    FALSE AS is_cti_entity
  FROM none_cti_entities
)

SELECT     
{{ generate_dimension_key('entity_name_ar') }} AS id,
*
FROM all_entities
ORDER BY id
