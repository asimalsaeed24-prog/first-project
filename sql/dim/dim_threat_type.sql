SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS threat_type_name

UNION ALL

SELECT
  id,
  label AS threat_type_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_threat_type'
