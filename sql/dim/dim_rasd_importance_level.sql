SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS importance_level,
  current_timestamp() AS created_at,
  current_timestamp() AS updated_at

UNION ALL

SELECT
  id,
  label AS importance_level,
  first_seen_at AS created_at,
  current_timestamp() AS updated_at
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_rasd_importance_level'
