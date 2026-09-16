-- Report threat groups are adversaries, so the report's group set resolves
-- against dim_cti_adversary on the CTI adversary_id. Values that are not a
-- CTI adversary_id stay unresolved and collapse into the unknown member.
WITH member_sets AS (
  SELECT DISTINCT
    group_group_key,
    group_members
  FROM {{ target_schema }}.stg_report
),

exploded AS (
  SELECT
    s.group_group_key,
    m.member
  FROM member_sets s
  LATERAL VIEW explode(s.group_members) m AS member
),

resolved AS (
  SELECT
    e.group_group_key,
    coalesce(d.id, -1) AS adversary_dim_id,
    min(e.member) AS member_value
  FROM exploded e
  LEFT JOIN {{ target_schema }}.dim_cti_adversary d
    ON e.member = upper(trim(d.adversary_id))
  GROUP BY
    e.group_group_key,
    coalesce(d.id, -1)
)

SELECT
  group_group_key,
  adversary_dim_id,
  member_value,
  count(*) OVER (PARTITION BY group_group_key) AS member_count,
  1.0 / count(*) OVER (PARTITION BY group_group_key) AS weight_factor,
  (adversary_dim_id = -1) AS is_unknown_member,
  current_timestamp() AS created_at,
  current_timestamp() AS updated_at
FROM resolved
