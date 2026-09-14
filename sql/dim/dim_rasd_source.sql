SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS source_name,
  current_timestamp() AS created_at,
  current_timestamp() AS updated_at

UNION ALL

SELECT
  id,
  label AS source_name,
  first_seen_at AS created_at,
  current_timestamp() AS updated_at
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_rasd_source'
