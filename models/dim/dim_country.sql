{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

WITH countries AS (


 SELECT DISTINCT
split_name as country_name
  FROM {{ source('cti', 'rasd') }}
  CROSS JOIN UNNEST(
    split(COALESCE(country, ''), ',')
  ) AS t(split_name)
where country  is not null


),


-- Add "unknown" country record
all_countries AS (
  SELECT
    -1 AS id,
    'Unknown' AS country_name
  
  UNION ALL
  
  SELECT
    {{ generate_dimension_key('country_name') }} AS id,
    country_name
  FROM countries
)

SELECT *
FROM all_countries
ORDER BY id
