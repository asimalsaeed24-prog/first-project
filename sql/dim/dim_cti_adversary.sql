SELECT
  CAST(-1 AS BIGINT) AS id,
  CAST(NULL AS STRING) AS adversary_id,
  'Unknown' AS adversary_name,
  lower(md5('Unknown')) AS country_group_key

UNION ALL

SELECT
  k.id,
  a.adversary_id,
  coalesce(a.adversary, k.label) AS adversary_name,
  a.country_group_key
FROM {{ target_schema }}.dim_key k
LEFT JOIN {{ target_schema }}.stg_adversary a
  ON a.adversary_id = k.natural_key
WHERE k.dimension = 'dim_cti_adversary'
