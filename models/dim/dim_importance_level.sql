{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

WITH raw_data AS (
  SELECT DISTINCT
    {{ clean_null_values('Importance') }} AS importance_level
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

valid_data AS (
  SELECT importance_level
  FROM raw_data
  WHERE importance_level IS NOT NULL
),

-- Add "unknown" importance level record
all_importance_levels AS (
  SELECT
    -1 AS id,
    'Unknown' AS importance_level
  
  UNION ALL
  
  SELECT
    {{ generate_dimension_key('importance_level') }} AS id,
    importance_level
  FROM valid_data
)

SELECT *
FROM all_importance_levels
ORDER BY id
