-- fact_report.country_group_key -> dim_country
--
-- A report can name several countries, so the fact carries a group key instead of
-- a foreign key and this bridge expands it. Reports naming the same set share
-- one key, so the bridge holds one row per distinct set, not per report.
--
-- Multiply a measure by weight_factor to split a report across its members and
-- keep totals additive. Join without it to answer membership questions.

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

-- Two members can resolve to the same row, so collapse them before counting or
-- the weights would not sum to 1.
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
