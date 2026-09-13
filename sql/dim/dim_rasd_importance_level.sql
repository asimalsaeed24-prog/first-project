SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS importance_level

UNION ALL

SELECT
  id,
  label AS importance_level
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_rasd_importance_level'
