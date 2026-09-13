CREATE TABLE IF NOT EXISTS {{ target_schema }}.dim_key (
  dimension STRING,
  natural_key STRING,
  label STRING,
  id BIGINT,
  first_seen_at TIMESTAMP
) USING DELTA;

INSERT INTO {{ target_schema }}.dim_key
WITH candidates AS (
  SELECT 'dim_rasd_classification' AS dimension, classification_name AS label
  FROM {{ target_schema }}.stg_report
  WHERE classification_name IS NOT NULL

  UNION ALL

  SELECT 'dim_cti_adversary' AS dimension, adversary_id
  FROM {{ target_schema }}.stg_adversary

  UNION ALL

  SELECT 'dim_rasd_evidence_type', evidence_type_name
  FROM {{ target_schema }}.stg_report
  WHERE evidence_type_name IS NOT NULL

  UNION ALL

  SELECT 'dim_rasd_importance_level', importance_level
  FROM {{ target_schema }}.stg_report
  WHERE importance_level IS NOT NULL

  UNION ALL

  SELECT 'dim_rasd_source', source_name
  FROM {{ target_schema }}.stg_report
  WHERE source_name IS NOT NULL

  UNION ALL

  SELECT 'dim_rasd_threat_type', threat_type_name
  FROM {{ target_schema }}.stg_report
  WHERE threat_type_name IS NOT NULL

  UNION ALL

  SELECT 'dim_country', trim(value)
  FROM {{ target_schema }}.stg_report
  LATERAL VIEW explode(country_labels) exploded AS value
  WHERE trim(value) <> ''

  UNION ALL

  SELECT 'dim_rasd_group', trim(value)
  FROM {{ target_schema }}.stg_report
  LATERAL VIEW explode(group_labels) exploded AS value
  WHERE trim(value) <> ''

  UNION ALL

  SELECT 'dim_rasd_entity', entity_natural_key
  FROM {{ target_schema }}.stg_entity
  WHERE entity_natural_key IS NOT NULL

  UNION ALL

  -- Country data from adversaries (shared dimension - dim_country)
  SELECT 'dim_country', trim(member)
  FROM {{ target_schema }}.stg_adversary
  LATERAL VIEW explode(country_members) exploded AS member
  WHERE trim(member) <> ''
),

normalized AS (
  SELECT
    dimension,
    upper(label) AS natural_key,
    min(label) AS label
  FROM candidates
  GROUP BY dimension, upper(label)
),

unseen AS (
  SELECT n.dimension, n.natural_key, n.label
  FROM normalized n
  WHERE NOT EXISTS (
    SELECT 1
    FROM {{ target_schema }}.dim_key existing
    WHERE existing.dimension = n.dimension
      AND existing.natural_key = n.natural_key
  )
),

high_water AS (
  SELECT dimension, max(id) AS max_id
  FROM {{ target_schema }}.dim_key
  GROUP BY dimension
)

SELECT
  unseen.dimension,
  unseen.natural_key,
  unseen.label,
  coalesce(high_water.max_id, 0)
    + row_number() OVER (PARTITION BY unseen.dimension ORDER BY unseen.natural_key) AS id,
  current_timestamp() AS first_seen_at
FROM unseen
LEFT JOIN high_water
  ON high_water.dimension = unseen.dimension
