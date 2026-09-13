-- Adversaries with their target countries
-- Shows direct relationships between adversaries and the countries they target
-- Based on CTI adversary data (not through reports)

SELECT
  a.adversary_id,
  a.adversary_name,
  a.country_group_key,
  
  c.id AS country_id,
  c.country_name,
  
  b.weight_factor,
  b.is_unknown_member,
  
  -- Count of countries targeted by this adversary (based on group key)
  COUNT(*) OVER (PARTITION BY a.adversary_id, a.country_group_key) AS total_targeted_countries

FROM {{ target_schema }}.dim_cti_adversary a

JOIN {{ target_schema }}.bridge_adversary_country b
  ON a.country_group_key = b.country_group_key
  AND a.adversary_id = b.adversary_id

JOIN {{ target_schema }}.dim_country c
  ON b.country_id = c.id

WHERE a.id <> -1
  AND c.id <> -1
  AND b.is_unknown_member = FALSE

ORDER BY 
  a.adversary_name,
  c.country_name