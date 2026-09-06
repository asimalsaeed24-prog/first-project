{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

WITH raw_data AS (
  SELECT DISTINCT
    {{ clean_null_values('Evidence_Type') }} AS evidence_type_name
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

valid_data AS (
  SELECT evidence_type_name
  FROM raw_data
  WHERE evidence_type_name IS NOT NULL
),

-- Add "unknown" evidence type record
all_evidence_types AS (
  SELECT
    -1 AS id,
    'Unknown' AS evidence_type_name
  
  UNION ALL
  
  SELECT
    {{ generate_dimension_key('evidence_type_name') }} AS id,
    evidence_type_name
  FROM valid_data
)

SELECT *
FROM all_evidence_types
ORDER BY id
