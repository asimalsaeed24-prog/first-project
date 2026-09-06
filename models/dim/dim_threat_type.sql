{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

WITH raw_data AS (
  SELECT DISTINCT
    {{ clean_null_values('Threat_Type') }} AS threat_type_name
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

valid_data AS (
  SELECT threat_type_name
  FROM raw_data
  WHERE threat_type_name IS NOT NULL
),

-- Add "unknown" threat type record
all_threat_types AS (
  SELECT
    -1 AS id,
    'Unknown' AS threat_type_name
  
  UNION ALL
  
  SELECT
    {{ generate_dimension_key('threat_type_name') }} AS id,
    threat_type_name
  FROM valid_data
)

SELECT *
FROM all_threat_types
ORDER BY id
