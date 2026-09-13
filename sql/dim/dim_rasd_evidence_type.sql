SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS evidence_type_name

UNION ALL

SELECT
  id,
  label AS evidence_type_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_rasd_evidence_type'
