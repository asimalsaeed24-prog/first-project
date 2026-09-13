
WITH adversary_countries AS (
  SELECT DISTINCT
    a.adversary_id,
    a.country_group_key,
    c.member AS country_value
  FROM {{ target_schema }}.stg_adversary a
  LATERAL VIEW explode(a.country_members) c AS member
  WHERE c.member IS NOT NULL 
    AND trim(c.member) <> ''
),

resolved AS (
  SELECT
    ac.adversary_id,
    ac.country_group_key,
    coalesce(d.id, -1) AS country_id,
    ac.country_value AS member_value,
    count(*) OVER (PARTITION BY ac.adversary_id, ac.country_group_key) AS member_count
  FROM adversary_countries ac
  LEFT JOIN {{ target_schema }}.dim_country d
    ON upper(trim(ac.country_value)) = upper(trim(d.country_name))
)

SELECT

  ac.country_group_key,
  ac.adversary_id,
  ac.country_id,
  ac.member_value,
  ac.member_count,
  1.0 / ac.member_count AS weight_factor,
  (ac.country_id = -1) AS is_unknown_member
  
FROM resolved ac