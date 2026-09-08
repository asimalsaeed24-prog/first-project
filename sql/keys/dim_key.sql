-- THE ONLY TABLE IN THIS WAREHOUSE THAT HOLDS STATE. BACK IT UP.
--
-- Every dimension's surrogate key lives here, one row per (dimension, value).
-- A value keeps the id it was first given for good, and a value that turns up
-- later gets the next id in its dimension. Nothing already in the table is ever
-- updated or deleted, so the business can report against these ids safely.
--
-- Before this, each dimension minted its own id with row_number() over an
-- alphabetical sort, so a new label inserted mid-alphabet shifted every id after
-- it. That is what this table exists to stop.
--
-- Everything else in the warehouse is derived and can be dropped and rebuilt at
-- any time. This table cannot -- rebuilding it re-mints every id.
--
--   dimension    which dimension the key belongs to
--   natural_key  upper-cased, what a value is matched on
--   label        the value as first written, what the dimension displays
--   id           the surrogate key, unique within its dimension, starts at 1
--
-- To add a dimension, add a branch to the candidates UNION below. Nothing else
-- needs to change.

CREATE TABLE IF NOT EXISTS {{ target_schema }}.dim_key (
  dimension STRING,
  natural_key STRING,
  label STRING,
  id BIGINT,
  first_seen_at TIMESTAMP
) USING DELTA;

INSERT INTO {{ target_schema }}.dim_key
WITH candidates AS (
  SELECT 'dim_classification' AS dimension, classification_name AS label
  FROM {{ target_schema }}.stg_report
  WHERE classification_name IS NOT NULL

  UNION ALL

  SELECT 'dim_evidence_type', evidence_type_name
  FROM {{ target_schema }}.stg_report
  WHERE evidence_type_name IS NOT NULL

  UNION ALL

  SELECT 'dim_importance_level', importance_level
  FROM {{ target_schema }}.stg_report
  WHERE importance_level IS NOT NULL

  UNION ALL

  SELECT 'dim_source', source_name
  FROM {{ target_schema }}.stg_report
  WHERE source_name IS NOT NULL

  UNION ALL

  SELECT 'dim_threat_type', threat_type_name
  FROM {{ target_schema }}.stg_report
  WHERE threat_type_name IS NOT NULL

  UNION ALL

  SELECT 'dim_country', trim(value)
  FROM {{ target_schema }}.stg_report
  LATERAL VIEW explode(country_labels) exploded AS value
  WHERE trim(value) <> ''

  UNION ALL

  SELECT 'dim_group', trim(value)
  FROM {{ target_schema }}.stg_report
  LATERAL VIEW explode(group_labels) exploded AS value
  WHERE trim(value) <> ''

  UNION ALL

  -- An entity is identified by its cti_id where it has one, so a client
  -- renaming itself keeps its key. stg_entity works that out.
  SELECT 'dim_entity', entity_natural_key
  FROM {{ target_schema }}.stg_entity
  WHERE entity_natural_key IS NOT NULL
),

-- One row per distinct value. min(label) settles two spellings of the same
-- value on one deterministic display form instead of flip-flopping run to run.
normalized AS (
  SELECT
    dimension,
    upper(label) AS natural_key,
    min(label) AS label
  FROM candidates
  GROUP BY dimension, upper(label)
),

-- Only values the table has never seen. Everything already in dim_key keeps the
-- id it has.
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

-- Where each dimension's numbering has got to.
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
