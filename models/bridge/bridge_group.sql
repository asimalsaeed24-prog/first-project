{{
  config(
    materialized='table',
    unique_key=['group_group_key', 'group_id'],
    tags=['gold', 'bridge']
  )
}}

-- Expands fact_report.group_group_key into the threat groups a report relates
-- to (cti.rasd.related_groups, comma separated).
--   fact_report -> bridge_group -> dim_group

WITH report_groups AS (
  SELECT DISTINCT
    {{ generate_bridge_key(report_group_source()) }} AS group_group_key,
    {{ normalize_bridge_members(report_group_source()) }} AS members
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),

group_members AS (
  SELECT
    group_group_key,
    member_token
  FROM report_groups
  {{ explode_array('members') }}
),

resolved AS (
  SELECT
    m.group_group_key,
    COALESCE(d.id, -1) AS group_id,
    MIN(m.member_token) AS member_value
  FROM group_members m
  LEFT JOIN {{ ref('dim_group') }} d
    ON m.member_token = UPPER(TRIM(d.group_name))
  GROUP BY
    m.group_group_key,
    COALESCE(d.id, -1)
)

SELECT
  group_group_key,
  group_id,
  member_value,
  COUNT(*) OVER (PARTITION BY group_group_key) AS member_count,
  1.0 / COUNT(*) OVER (PARTITION BY group_group_key) AS weight_factor,
  (group_id = -1) AS is_unknown_member
FROM resolved
