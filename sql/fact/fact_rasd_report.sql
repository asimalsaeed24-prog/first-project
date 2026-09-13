WITH report_data AS (
  SELECT
    r.report_id,
    r.title,
    r.description,
    r.actions,
    r.analysis,

    r.creation_date,
    r.publication_date,
    r.report_date,
    r.updated_at,

    coalesce(classification_dim.id, -1) AS classification_id,
    coalesce(evidence_type_dim.id, -1)  AS evidence_type_id,
    coalesce(importance_dim.id, -1)     AS importance_level_id,
    coalesce(source_dim.id, -1)         AS source_id,
    coalesce(threat_type_dim.id, -1)    AS threat_type_id,

    r.country_group_key,
    r.entity_group_key,
    r.group_group_key,
    r.adversary_group_key

  FROM {{ target_schema }}.stg_report r

  LEFT JOIN {{ target_schema }}.dim_rasd_classification classification_dim
    ON r.classification_name = classification_dim.classification_name

  LEFT JOIN {{ target_schema }}.dim_rasd_evidence_type evidence_type_dim
    ON r.evidence_type_name = evidence_type_dim.evidence_type_name

  LEFT JOIN {{ target_schema }}.dim_rasd_importance_level importance_dim
    ON r.importance_level = importance_dim.importance_level

  LEFT JOIN {{ target_schema }}.dim_rasd_source source_dim
    ON r.source_name = source_dim.source_name

  LEFT JOIN {{ target_schema }}.dim_rasd_threat_type threat_type_dim
    ON r.threat_type_name = threat_type_dim.threat_type_name
)

SELECT
  row_number() OVER (ORDER BY report_id) AS id,
  report_id,
  title,
  description,
  actions,
  analysis,

  creation_date,
  publication_date,
  report_date,
  updated_at,

  classification_id,
  evidence_type_id,
  importance_level_id,
  source_id,
  threat_type_id,

  country_group_key,
  entity_group_key,
  group_group_key,
  adversary_group_key

FROM report_data
