SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS group_name

UNION ALL

SELECT
  id,
  label AS group_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_rasd_group'
