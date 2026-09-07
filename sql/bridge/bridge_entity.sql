-- fact_report.entity_group_key -> dim_entity
--
-- Members arrive as whichever identifier the report carried, so they are
-- matched against dim_entity in preference order -- cti_id, prm_id, Arabic
-- label, English label -- and the first match wins. A label that happens to
-- equal some other entity's id therefore cannot outrank a real id match.
--
-- entities_rasd_id has no counterpart in cti.entities, so those members land on
-- id = -1 and stay countable through is_unknown_member instead of disappearing.
-- That is the "RASD id on the report but no CTI id" cohort.

CREATE OR REPLACE TABLE {{ target_schema }}.bridge_entity USING delta AS

WITH member_sets AS (
  SELECT DISTINCT
    entity_group_key,
    entity_members
  FROM {{ target_schema }}.stg_report
),

exploded AS (
  SELECT
    s.entity_group_key,
    m.member
  FROM member_sets s
  LATERAL VIEW explode(s.entity_members) m AS member
),

-- Every way an entity can be named, ranked by how trustworthy that way is.
match_candidates AS (
  SELECT upper(trim(cti_id)) AS member, id AS entity_id, 1 AS priority
  FROM {{ target_schema }}.dim_entity
  WHERE cti_id IS NOT NULL AND trim(cti_id) <> ''

  UNION ALL

  SELECT upper(trim(prm_id)) AS member, id AS entity_id, 2 AS priority
  FROM {{ target_schema }}.dim_entity
  WHERE prm_id IS NOT NULL AND trim(prm_id) <> ''

  UNION ALL

  SELECT upper(trim(entity_name_ar)) AS member, id AS entity_id, 3 AS priority
  FROM {{ target_schema }}.dim_entity
  WHERE entity_name_ar IS NOT NULL AND trim(entity_name_ar) <> ''

  UNION ALL

  SELECT upper(trim(entity_name_en)) AS member, id AS entity_id, 4 AS priority
  FROM {{ target_schema }}.dim_entity
  WHERE entity_name_en IS NOT NULL AND trim(entity_name_en) <> ''
),

entity_lookup AS (
  SELECT member, entity_id
  FROM (
    SELECT
      member,
      entity_id,
      row_number() OVER (PARTITION BY member ORDER BY priority, entity_id) AS row_num
    FROM match_candidates
  ) ranked
  WHERE row_num = 1
),

-- An id member and a label member can name the same entity, so collapse them
-- before counting or the weights would not sum to 1.
resolved AS (
  SELECT
    e.entity_group_key,
    coalesce(l.entity_id, -1) AS entity_id,
    min(e.member) AS member_value
  FROM exploded e
  LEFT JOIN entity_lookup l
    ON e.member = l.member
  GROUP BY
    e.entity_group_key,
    coalesce(l.entity_id, -1)
)

SELECT
  entity_group_key,
  entity_id,
  member_value,
  count(*) OVER (PARTITION BY entity_group_key) AS member_count,
  1.0 / count(*) OVER (PARTITION BY entity_group_key) AS weight_factor,
  (entity_id = -1) AS is_unknown_member
FROM resolved
