WITH member_sets AS (
  SELECT DISTINCT
    country_group_key,
    country_members
  FROM {{ target_schema }}.stg_report
),

exploded AS (
  SELECT
    s.country_group_key,
    m.member
  FROM member_sets s
  LATERAL VIEW explode(s.country_members) m AS member
),

resolved AS (
  SELECT
    e.country_group_key,
    coalesce(d.id, -1) AS country_id,
    min(e.member) AS member_value
  FROM exploded e
  LEFT JOIN {{ target_schema }}.dim_country d
    ON e.member = upper(trim(d.country_name))
  GROUP BY
    e.country_group_key,
    coalesce(d.id, -1)
)

SELECT
  country_group_key,
  country_id,
  member_value,
  count(*) OVER (PARTITION BY country_group_key) AS member_count,
  1.0 / count(*) OVER (PARTITION BY country_group_key) AS weight_factor,
  (country_id = -1) AS is_unknown_member
FROM resolved
