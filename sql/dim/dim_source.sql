SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS source_name

UNION ALL

SELECT
  id,
  label AS source_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_source'
