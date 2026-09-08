-- fact_report.group_group_key -> dim_group
--
-- A report can name several threat groups, so the fact carries a group key instead of
-- a foreign key and this bridge expands it. Reports naming the same set share
-- one key, so the bridge holds one row per distinct set, not per report.
--
-- Multiply a measure by weight_factor to split a report across its members and
-- keep totals additive. Join without it to answer membership questions.

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

-- Two members can resolve to the same row, so collapse them before counting or
-- the weights would not sum to 1.
resolved AS (
  SELECT
    e.group_group_key,
    coalesce(d.id, -1) AS group_id,
    min(e.member) AS member_value
  FROM exploded e
  LEFT JOIN {{ target_schema }}.dim_group d
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
