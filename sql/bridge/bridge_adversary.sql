WITH member_sets AS (
  SELECT DISTINCT
    adversary_group_key,
    adversary_members
  FROM {{ target_schema }}.stg_report
  WHERE adversary_members IS NOT NULL
    AND size(adversary_members) > 0
),

exploded AS (
  SELECT
    s.adversary_group_key,
    m.member AS adversary_member
  FROM member_sets s
  LATERAL VIEW explode(s.adversary_members) m AS member
),

resolved AS (
  SELECT
    e.adversary_group_key,
    coalesce(d.id, -1) AS adversary_dim_id,
    min(e.adversary_member) AS member_value
  FROM exploded e
  LEFT JOIN {{ target_schema }}.dim_cti_adversary d
    ON e.adversary_member = d.adversary_id
  GROUP BY
    e.adversary_group_key,
    coalesce(d.id, -1)
)

SELECT
  adversary_group_key,
  adversary_dim_id,
  member_value,
  count(*) OVER (PARTITION BY adversary_group_key) AS member_count,
  1.0 / count(*) OVER (PARTITION BY adversary_group_key) AS weight_factor,
  (adversary_dim_id = -1) AS is_unknown_member
FROM resolved

