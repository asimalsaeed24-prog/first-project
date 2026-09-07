{{
  config(
    materialized='table',
    unique_key=['entity_group_key', 'entity_id'],
    tags=['gold', 'bridge']
  )
}} 

-- Expands fact_report.entity_group_key into the entities a report is about.
--   fact_report -> bridge_entity -> dim_entity
-- Members arrive as whichever identifier the report carried, so they are
-- resolved against dim_entity in preference order: cti_id, then prm_id, then
-- the Arabic label, then the English one. The first match wins, so a label that
-- happens to equal some other entity's id cannot outrank a real id match.

WITH report_groups AS (
  SELECT DISTINCT
    {{ generate_bridge_key(report_entity_source(), delimiter='|') }} AS entity_group_key,
    {{ normalize_bridge_members(report_entity_source(), delimiter='|') }} AS members
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

group_members AS (
  SELECT
    entity_group_key,
    member_token
  FROM report_groups
  {{ explode_array('members') }}
),

-- One row per way an entity can be named, ranked by how trustworthy that way is.
match_candidates AS (
  SELECT UPPER(TRIM(cti_id)) AS match_key, id AS entity_id, 1 AS priority
  FROM {{ ref('dim_entity') }}
  WHERE cti_id IS NOT NULL AND TRIM(cti_id) <> ''

  UNION ALL

  SELECT UPPER(TRIM(prm_id)) AS match_key, id AS entity_id, 2 AS priority
  FROM {{ ref('dim_entity') }}
  WHERE prm_id IS NOT NULL AND TRIM(prm_id) <> ''

  UNION ALL

  SELECT UPPER(TRIM(entity_name_ar)) AS match_key, id AS entity_id, 3 AS priority
  FROM {{ ref('dim_entity') }}
  WHERE entity_name_ar IS NOT NULL AND TRIM(entity_name_ar) <> ''

  UNION ALL

  SELECT UPPER(TRIM(entity_name_en)) AS match_key, id AS entity_id, 4 AS priority
  FROM {{ ref('dim_entity') }}
  WHERE entity_name_en IS NOT NULL AND TRIM(entity_name_en) <> ''
),

entity_lookup AS (
  SELECT match_key, entity_id
  FROM (
    SELECT
      match_key,
      entity_id,
      ROW_NUMBER() OVER (PARTITION BY match_key ORDER BY priority, entity_id) AS rn
    FROM match_candidates
  ) ranked
  WHERE rn = 1
),

-- An id token and a label token can name the same entity; collapse them so the
-- weights still sum to 1.
resolved AS (
  SELECT
    m.entity_group_key,
    COALESCE(l.entity_id, -1) AS entity_id,
    MIN(m.member_token) AS member_value
  FROM group_members m
  LEFT JOIN entity_lookup l
    ON m.member_token = l.match_key
  GROUP BY
    m.entity_group_key,
    COALESCE(l.entity_id, -1)
)

SELECT
  entity_group_key,
  entity_id,
  member_value,
  COUNT(*) OVER (PARTITION BY entity_group_key) AS member_count,
  1.0 / COUNT(*) OVER (PARTITION BY entity_group_key) AS weight_factor,
  (entity_id = -1) AS is_unknown_member
FROM resolved
