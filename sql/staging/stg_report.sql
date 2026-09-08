WITH raw_reports AS (
  SELECT *
  FROM {{ source_schema }}.rasd
  WHERE report_type = 'rasd'
),

identifiers AS (
  SELECT
    *,

    coalesce(
      nullif(trim(entities_cti_id), ''),
      nullif(trim(entities_prm_id), ''),
      nullif(trim(entities_rasd_id), ''),
      nullif(trim(entities_names_ar), '')
    ) AS entity_source,
    nullif(trim(creation_date), '') AS raw_creation_date,
    nullif(trim(publication_date), '') AS raw_publication_date,
    nullif(trim(report_date), '') AS raw_report_date,
    nullif(trim(updated_at), '') AS raw_updated_at
  FROM raw_reports
),

tokenized AS (
  SELECT
    *,
    filter(transform(split(coalesce(country, ''), ','), x -> upper(trim(x))), x -> x <> '') AS country_tokens,
    filter(transform(split(coalesce(entity_source, ''), '\\|'), x -> upper(trim(x))), x -> x <> '') AS entity_tokens,
    filter(transform(split(coalesce(related_groups, ''), ','), x -> upper(trim(x))), x -> x <> '') AS group_tokens,
    array_distinct(filter(transform(split(coalesce(country, ''), ','), x -> trim(x)), x -> x <> '')) AS country_labels,
    array_distinct(filter(transform(split(coalesce(related_groups, ''), ','), x -> trim(x)), x -> x <> '')) AS group_labels
  FROM identifiers
),

member_sets AS (
  SELECT
    *,
    CASE WHEN size(country_tokens) = 0 THEN array('UNKNOWN') ELSE array_sort(array_distinct(country_tokens)) END AS country_members,
    CASE WHEN size(entity_tokens) = 0 THEN array('UNKNOWN') ELSE array_sort(array_distinct(entity_tokens)) END AS entity_members,
    CASE WHEN size(group_tokens) = 0 THEN array('UNKNOWN') ELSE array_sort(array_distinct(group_tokens)) END AS group_members
  FROM tokenized
)

SELECT
  id AS report_id,
  title,
  description,
  actions,
  analysis,

  to_date(coalesce(
    to_timestamp(raw_creation_date),
    to_timestamp(raw_creation_date, 'dd/MM/yyyy HH:mm:ss'),
    to_timestamp(raw_creation_date, 'dd/MM/yyyy'),
    to_timestamp(raw_creation_date, 'MM/dd/yyyy')
  )) AS creation_date,

  to_date(coalesce(
    to_timestamp(raw_publication_date),
    to_timestamp(raw_publication_date, 'dd/MM/yyyy HH:mm:ss'),
    to_timestamp(raw_publication_date, 'dd/MM/yyyy'),
    to_timestamp(raw_publication_date, 'MM/dd/yyyy')
  )) AS publication_date,

  to_date(coalesce(
    to_timestamp(raw_report_date),
    to_timestamp(raw_report_date, 'dd/MM/yyyy HH:mm:ss'),
    to_timestamp(raw_report_date, 'dd/MM/yyyy'),
    to_timestamp(raw_report_date, 'MM/dd/yyyy')
  )) AS report_date,

  coalesce(
    to_timestamp(raw_updated_at),
    to_timestamp(raw_updated_at, 'dd/MM/yyyy HH:mm:ss'),
    to_timestamp(raw_updated_at, 'dd/MM/yyyy'),
    to_timestamp(raw_updated_at, 'MM/dd/yyyy')
  ) AS updated_at,

  CASE WHEN upper(trim(classification))     IN ('NULL', 'NUL', '') THEN NULL ELSE trim(classification)     END AS classification_name,
  CASE WHEN upper(trim(evidence_type))      IN ('NULL', 'NUL', '') THEN NULL ELSE trim(evidence_type)      END AS evidence_type_name,
  CASE WHEN upper(trim(importance))         IN ('NULL', 'NUL', '') THEN NULL ELSE trim(importance)         END AS importance_level,
  CASE WHEN upper(trim(observation_source)) IN ('NULL', 'NUL', '') THEN NULL ELSE trim(observation_source) END AS source_name,
  CASE WHEN upper(trim(threat_type))        IN ('NULL', 'NUL', '') THEN NULL ELSE trim(threat_type)        END AS threat_type_name,

  country_members,
  entity_members,
  group_members,

  country_labels,
  group_labels,

  lower(md5(array_join(country_members, '|'))) AS country_group_key,
  lower(md5(array_join(entity_members, '|')))  AS entity_group_key,
  lower(md5(array_join(group_members, '|')))   AS group_group_key

FROM member_sets
