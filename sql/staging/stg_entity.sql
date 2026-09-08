-- Every entity a report can be about, with the natural key its surrogate id is
-- minted from. Two populations:
--
--   * registered CTI entities, which carry a cti_id and the full attribute set
--   * label-only entities, named on a report but never registered
--
-- dim_key mints ids from this model and dim_entity reads it back for the
-- attributes, so the entity list and the ids assigned to it can never be
-- derived from different logic.

WITH cti_entities AS (
  SELECT
    trim(cti_id) AS cti_id,
    CASE WHEN upper(trim(prm_id))         IN ('NULL', 'NUL', '') THEN NULL ELSE trim(prm_id)         END AS prm_id,
    CASE WHEN upper(trim(client_name_en)) IN ('NULL', 'NUL', '') THEN NULL ELSE trim(client_name_en) END AS entity_name_en,
    CASE WHEN upper(trim(client_name_ar)) IN ('NULL', 'NUL', '') THEN NULL ELSE trim(client_name_ar) END AS entity_name_ar,
    CASE WHEN upper(trim(country))        IN ('NULL', 'NUL', '') THEN NULL ELSE trim(country)        END AS country,
    CASE WHEN upper(trim(category))       IN ('NULL', 'NUL', '') THEN NULL ELSE trim(category)       END AS category,
    CASE WHEN upper(trim(sector))         IN ('NULL', 'NUL', '') THEN NULL ELSE trim(sector)         END AS sector,
    CASE WHEN upper(trim(type_of_entity)) IN ('NULL', 'NUL', '') THEN NULL ELSE trim(type_of_entity) END AS entity_type,
    CASE WHEN upper(trim(domain))         IN ('NULL', 'NUL', '') THEN NULL ELSE trim(domain)         END AS domain,
    true AS is_cti_entity
  FROM {{ source_schema }}.entities
  WHERE cti_id IS NOT NULL
),

-- One row per cti_id.
registered AS (
  SELECT
    cti_id, prm_id, entity_name_en, entity_name_ar,
    country, category, sector, entity_type, domain, is_cti_entity
  FROM (
    SELECT
      *,
      row_number() OVER (PARTITION BY cti_id ORDER BY entity_name_en) AS row_num
    FROM cti_entities
  ) ranked
  WHERE row_num = 1
),

-- entities_names_ar is pipe separated. '\\|' because split() takes a regex.
report_labels AS (
  SELECT DISTINCT
    trim(value) AS entity_name_ar
  FROM {{ source_schema }}.rasd
  LATERAL VIEW explode(split(coalesce(entities_names_ar, ''), '\\|')) exploded AS value
  WHERE report_type = 'rasd'
    AND entities_cti_id IS NULL
    AND trim(value) <> ''
),

label_only AS (
  SELECT
    CAST(NULL AS STRING) AS cti_id,
    CAST(NULL AS STRING) AS prm_id,
    l.entity_name_ar AS entity_name_en,  -- the source carries no English label here
    l.entity_name_ar,
    CAST(NULL AS STRING) AS country,
    CAST(NULL AS STRING) AS category,
    CAST(NULL AS STRING) AS sector,
    CAST(NULL AS STRING) AS entity_type,
    CAST(NULL AS STRING) AS domain,
    false AS is_cti_entity
  FROM report_labels l
  WHERE NOT EXISTS (
    SELECT 1
    FROM registered r
    WHERE upper(r.entity_name_ar) = upper(l.entity_name_ar)
  )
),

all_entities AS (
  SELECT * FROM registered
  UNION ALL
  SELECT * FROM label_only
)

SELECT
  -- What the id is minted from. cti_id for a registered entity, so a client
  -- renaming itself keeps its key. A label-only entity has nothing but its
  -- name, so renaming one does mint a new key -- the source carries no
  -- identifier that would tie the old name to the new one.
  upper(coalesce(cti_id, entity_name_ar)) AS entity_natural_key,
  cti_id,
  prm_id,
  entity_name_en,
  entity_name_ar,
  country,
  category,
  sector,
  entity_type,
  domain,
  is_cti_entity
FROM all_entities
