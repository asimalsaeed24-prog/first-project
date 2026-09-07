{{
  config(
    materialized='table',
    unique_key=['country_group_key', 'country_id'],
    tags=['gold', 'bridge']
  )
}}

-- A report can name several countries, so fact_report carries a
-- country_group_key instead of a country_id and this bridge expands it.
--   fact_report -> bridge_country -> dim_country
-- Multiply a measure by weight_factor to split a report evenly across its
-- countries and keep totals additive; join without it to answer "which reports
-- mention Saudi Arabia".

WITH report_groups AS (
  SELECT DISTINCT
    {{ generate_bridge_key(report_country_source()) }} AS country_group_key,
    {{ normalize_bridge_members(report_country_source()) }} AS members
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

group_members AS (
  SELECT
    country_group_key,
    member_token
  FROM report_groups
  {{ explode_array('members') }}
),

-- Distinct tokens can land on the same country, so collapse them before
-- counting -- otherwise the weights would not sum to 1.
resolved AS (
  SELECT
    m.country_group_key,
    COALESCE(d.id, -1) AS country_id,
    MIN(m.member_token) AS member_value
  FROM group_members m
  LEFT JOIN {{ ref('dim_country') }} d
    ON m.member_token = UPPER(TRIM(d.country_name))
  GROUP BY
    m.country_group_key,
    COALESCE(d.id, -1)
)

SELECT
  country_group_key,
  country_id,
  member_value,
  COUNT(*) OVER (PARTITION BY country_group_key) AS member_count,
  1.0 / COUNT(*) OVER (PARTITION BY country_group_key) AS weight_factor,
  (country_id = -1) AS is_unknown_member
FROM resolved
