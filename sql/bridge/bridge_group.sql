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
    coalesce(d.id, -1) AS group_id,
    min(e.member) AS member_value
  FROM exploded e
  LEFT JOIN {{ target_schema }}.dim_rasd_group d
    ON e.member = upper(trim(d.group_name))
  GROUP BY
    e.group_group_key,
    coalesce(d.id, -1)
)

SELECT
  group_group_key,
  group_id,
  member_value,
  count(*) OVER (PARTITION BY group_group_key) AS member_count,
  1.0 / count(*) OVER (PARTITION BY group_group_key) AS weight_factor,
  (group_id = -1) AS is_unknown_member
FROM resolved
