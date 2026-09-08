-- The spine of the semantic layer: one row per report, with every
-- single-valued dimension already resolved to its name. Nobody outside the
-- warehouse should have to know an id or write a join to answer "what
-- classification was this report".
--
-- The joins are INNER on purpose and cannot drop a report: fact_report resolves
-- an unmatched or NULL attribute to id = -1, and every dimension carries that
-- row. If a report ever goes missing here, a dimension has lost its -1 row.
--
-- The three *_group_key columns are kept so the views below can fan out through
-- the bridges. Ignore them unless you are joining a bridge.

SELECT
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
  f.group_group_key

FROM {{ target_schema }}.fact_report f

JOIN {{ target_schema }}.dim_classification classification
  ON f.classification_id = classification.id

JOIN {{ target_schema }}.dim_evidence_type evidence_type
  ON f.evidence_type_id = evidence_type.id

JOIN {{ target_schema }}.dim_importance_level importance
  ON f.importance_level_id = importance.id

JOIN {{ target_schema }}.dim_source observation_source
  ON f.source_id = observation_source.id

JOIN {{ target_schema }}.dim_threat_type threat_type
  ON f.threat_type_id = threat_type.id
