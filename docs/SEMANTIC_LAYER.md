# CTI / RASD — Semantic Layer

The semantic layer is the set of views in the `cti_gold` schema that reporting and applications query.

## vw_report

One row per RASD report, with its classification attributes shown as labels.

| Column | Data Type | Description |
|---|---|---|
| id | INT | Report surrogate key. |
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| description | STRING | Report description. |
| actions | STRING | Recommended or taken actions. |
| analysis | STRING | Analyst assessment. |
| creation_date | DATE | Date the report was created. |
| publication_date | DATE | Date the report was published. |
| report_date | DATE | Report observation date. |
| updated_at | TIMESTAMP | Last update time in the source. |
| classification | STRING | Report classification. |
| evidence_type | STRING | Type of supporting evidence. |
| importance | STRING | Importance level. |
| observation_source | STRING | Source of the observation. |
| threat_type | STRING | Threat category. |
| country_group_key | STRING | Key of the report's country set. |
| entity_group_key | STRING | Key of the report's entity set. |
| group_group_key | STRING | Key of the report's threat group set. |
| adversary_group_key | STRING | Key of the report's adversary set. |

## vw_report_country

One row per report and country.

| Column | Data Type | Description |
|---|---|---|
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| report_date | DATE | Report observation date. |
| classification | STRING | Report classification. |
| importance | STRING | Importance level. |
| threat_type | STRING | Threat category. |
| country_id | BIGINT | Country surrogate key. |
| country_name | STRING | Country name. |
| weight_factor | DECIMAL | Share of the report assigned to this country. |
| is_unknown_member | BOOLEAN | True when the country is missing or unmatched. |

## vw_report_entity

One row per report and entity.

| Column | Data Type | Description |
|---|---|---|
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| report_date | DATE | Report observation date. |
| classification | STRING | Report classification. |
| importance | STRING | Importance level. |
| threat_type | STRING | Threat category. |
| entity_id | BIGINT | Entity surrogate key. |
| entity_name_en | STRING | Entity name in English. |
| entity_name_ar | STRING | Entity name in Arabic. |
| cti_id | STRING | Entity identifier in the CTI register. |
| prm_id | STRING | Entity identifier in PRM. |
| sector | STRING | Entity sector. |
| category | STRING | Entity category. |
| entity_type | STRING | Entity type. |
| entity_country | STRING | Country of the entity. |
| is_cti_entity | BOOLEAN | True when the entity exists in the CTI register. |
| weight_factor | DECIMAL | Share of the report assigned to this entity. |
| is_unknown_member | BOOLEAN | True when the entity is missing or unmatched. |

## vw_report_group

One row per report and threat group.

| Column | Data Type | Description |
|---|---|---|
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| report_date | DATE | Report observation date. |
| classification | STRING | Report classification. |
| importance | STRING | Importance level. |
| threat_type | STRING | Threat category. |
| group_id | BIGINT | Threat group surrogate key. |
| group_name | STRING | Threat group name. |
| weight_factor | DECIMAL | Share of the report assigned to this group. |
| is_unknown_member | BOOLEAN | True when the group is missing or unmatched. |

## vw_report_adversary

One row per report and CTI adversary.

| Column | Data Type | Description |
|---|---|---|
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| report_date | DATE | Report observation date. |
| classification | STRING | Report classification. |
| importance | STRING | Importance level. |
| threat_type | STRING | Threat category. |
| adversary_id | BIGINT | Adversary surrogate key. |
| adversary_name | STRING | Adversary name. |
| weight_factor | DECIMAL | Share of the report assigned to this adversary. |
| is_unknown_member | BOOLEAN | True when no adversary is linked or it is unmatched. |

## vw_adversary_target_country

One row per CTI adversary and target country.

| Column | Data Type | Description |
|---|---|---|
| adversary_id | STRING | Adversary identifier in CTI. |
| adversary_name | STRING | Adversary name. |
| country_group_key | STRING | Key of the adversary's target country set. |
| country_id | BIGINT | Country surrogate key. |
| country_name | STRING | Target country name. |
| weight_factor | DECIMAL | Share of the adversary assigned to this country. |
| is_unknown_member | BOOLEAN | True when the country is unmatched. |
| total_targeted_countries | BIGINT | Number of countries targeted by the adversary. |

## vw_entity_coverage

One row per entity coverage metric.

| Column | Data Type | Description |
|---|---|---|
| metric | STRING | Metric name. |
| value | BIGINT | Metric value. |
