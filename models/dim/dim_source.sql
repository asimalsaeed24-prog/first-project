{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

WITH raw_data AS (
  SELECT DISTINCT
    {{ clean_null_values('Observation_Source') }} AS source_name
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

valid_data AS (
  SELECT source_name
  FROM raw_data
  WHERE source_name IS NOT NULL
),

-- Add "unknown" source record
all_sources AS (
  SELECT
    -1 AS id,
    'Unknown' AS source_name
  
  UNION ALL
  
  SELECT
    {{ generate_dimension_key('source_name') }} AS id,
    source_name
  FROM valid_data
)

SELECT *
FROM all_sources
ORDER BY id
