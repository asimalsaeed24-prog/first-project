{{ config(
    materialized='delta_table',
    tags=['gold', 'dimension'],
    type='delta',
    tblproperties={
        'table_type': 'DELTA'
    }
) }}

    
WITH raw_data AS (
  SELECT DISTINCT
    {{ clean_null_values('Classification') }} AS classification_name
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

valid_data AS (
  SELECT classification_name
  FROM raw_data
  WHERE classification_name IS NOT NULL
),

-- Add "unknown" classification record
all_classifications AS (
  SELECT
    -1 AS id,
    'Unknown' AS classification_name
  
  UNION ALL
  
  SELECT
    {{ generate_dimension_key('classification_name') }} AS id,
    classification_name
  FROM valid_data
)

SELECT *
FROM all_classifications
ORDER BY id
