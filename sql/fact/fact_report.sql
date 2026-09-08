-- One row per RASD report.
--
-- Single-valued attributes resolve to a dimension id here. Country, entity and
-- related groups are multi-valued, so they keep the group key computed in
-- stg_report and join through their bridge -- a country_id on the fact could
-- only ever keep one of a report's countries.
--
-- Names that are NULL or unmatched fall to id = -1, so no foreign key is NULL.

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
  r.group_group_key

FROM {{ target_schema }}.stg_report r

LEFT JOIN {{ target_schema }}.dim_classification classification_dim
  ON r.classification_name = classification_dim.classification_name

LEFT JOIN {{ target_schema }}.dim_evidence_type evidence_type_dim
  ON r.evidence_type_name = evidence_type_dim.evidence_type_name

LEFT JOIN {{ target_schema }}.dim_importance_level importance_dim
  ON r.importance_level = importance_dim.importance_level

LEFT JOIN {{ target_schema }}.dim_source source_dim
  ON r.source_name = source_dim.source_name

LEFT JOIN {{ target_schema }}.dim_threat_type threat_type_dim
  ON r.threat_type_name = threat_type_dim.threat_type_name
