SELECT
  f.id,
  f.report_id,
  f.title,
  f.description,
  f.actions,
  f.analysis,

  f.creation_date,
  f.publication_date,
  f.report_date,
  f.updated_at,

  classification.classification_name AS classification,
  evidence_type.evidence_type_name   AS evidence_type,
  importance.importance_level        AS importance,
  observation_source.source_name     AS observation_source,
  threat_type.threat_type_name       AS threat_type,

  f.country_group_key,
  f.entity_group_key,
  f.group_group_key,
  f.adversary_group_key

FROM {{ target_schema }}.fact_rasd_report f

JOIN {{ target_schema }}.dim_rasd_classification classification
  ON f.classification_id = classification.id

JOIN {{ target_schema }}.dim_rasd_evidence_type evidence_type
  ON f.evidence_type_id = evidence_type.id

JOIN {{ target_schema }}.dim_rasd_importance_level importance
  ON f.importance_level_id = importance.id

JOIN {{ target_schema }}.dim_rasd_source observation_source
  ON f.source_id = observation_source.id

JOIN {{ target_schema }}.dim_rasd_threat_type threat_type
  ON f.threat_type_id = threat_type.id
