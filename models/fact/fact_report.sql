{{
  config(
    materialized='table',
    unique_key='report_id'
  )
}}

WITH raw_data AS (
  SELECT
    ID AS report_id,
    Title,
    Description,
    Actions,
    Analysis,
    
    {{ safe_cast_date('Creation_Date') }} AS creation_date,
    {{ safe_cast_date('Publication_Date') }} AS publication_date,
    {{ safe_cast_date('Report_Date') }} AS report_date,
    {{ safe_cast_date('Updated_At') }} AS updated_at,
    
    -- Dimension references
    Classification,    
    Evidence_Type,
    {{ clean_null_values('Importance') }} AS importance_level,    
    Observation_Source,
    Threat_Type,
    
  FROM {{ source('cti', 'rasd') }}
  WHERE Report_Type = 'rasd'
),
-- Join with dimension tables
fact_data AS (
  SELECT
    r.report_id,
    r.Title,
    r.Description,
    r.Actions,
    r.Analysis,
    r.creation_date,
    r.publication_date,
    r.report_date,
    r.updated_at,
    
    -- Dimension foreign keys
    cl.id AS classification_id,
    co.id AS country_id,
    e.id AS entity_id,
    et.id AS evidence_type_id,
    il.id AS importance_level_id,
    s.id AS source_id,
    tt.id AS threat_type_id

    {{ generate_bridge_key('country') }},
    {{ generate_bridge_key('country') }},
    {{ generate_bridge_key('country') }}
    
  FROM raw_data r
  LEFT JOIN {{ ref('dim_cti_rasd_classification') }} cl 
    ON COALESCE(r.Classification, 'Unknown') = cl.classification_name
  LEFT JOIN {{ ref('dim_cti_rasd_country') }} co 
    ON COALESCE(r.Country, 'Unknown') = co.country_name
  LEFT JOIN {{ ref('dim_cti_rasd_entity') }} e 
    ON r.entity_hash_key = e.entity_hash_key
  LEFT JOIN {{ ref('dim_cti_rasd_evidence_type') }} et 
    ON COALESCE(r.Evidence_Type, 'Unknown') = et.evidence_type_name
  LEFT JOIN {{ ref('dim_cti_rasd_importance_level') }} il 
    ON COALESCE(r.importance_level, 'Unknown') = il.importance_level
  LEFT JOIN {{ ref('dim_cti_rasd_source') }} s 
    ON COALESCE(r.Observation_Source, 'Unknown') = s.source_name
  LEFT JOIN {{ ref('dim_cti_rasd_threat_type') }} tt 
    ON COALESCE(r.Threat_Type, 'Unknown') = tt.threat_type_name
)

SELECT *
FROM fact_data

Subject: Current Summary of CTI Entity Data

Dear Team,

The following breakdown presents the latest figures from our CTI entity analysis:

Total CTI Entities: 5,386
CTI Entities Integrated with PRM: 2,609
Entities with a RASD Identifier on the Report but No CTI Identifier: 186
Entities with No Identifier (Label Only): 6
These numbers reflect the current state as of now and highlight both integration progress and areas requiring further attention.

Please let me know if you would like a more detailed review or updated insights.