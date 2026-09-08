SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS country_name

UNION ALL

SELECT
  id,
  label AS country_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_country'
