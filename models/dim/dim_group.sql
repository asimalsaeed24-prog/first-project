{{
  config(
    materialized='table',
    unique_key='id'
  )
}}

-- Threat groups named on a report (cti.rasd.related_groups, comma separated).
-- Added because bridge_group had no dimension to resolve its members against.

WITH groups AS (
  SELECT DISTINCT
    TRIM(split_name) AS group_name
  FROM {{ source('cti', 'rasd') }}
  {{ explode_array("split(coalesce(related_groups, ''), ',')", 't', 'split_name') }}
  WHERE Report_Type = 'rasd'
    AND related_groups IS NOT NULL
    AND TRIM(split_name) <> ''
),

-- Add "unknown" group record
all_groups AS (
  SELECT
    -1 AS id,
    'Unknown' AS group_name

  UNION ALL

  SELECT
    {{ generate_dimension_key('group_name') }} AS id,
    group_name
  FROM groups
)

SELECT *
FROM all_groups
ORDER BY id
