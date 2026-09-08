SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS classification_name

UNION ALL

SELECT
  id,
  label AS classification_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_classification'
