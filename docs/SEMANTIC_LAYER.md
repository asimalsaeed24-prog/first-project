# CTI / RASD — Semantic Layer

The semantic layer is the set of views in the `cti_gold` schema that reporting tools, analysts and the Django application read. Every view resolves surrogate keys into readable names and flattens the many-to-many links, so nothing outside this layer needs to join a bridge table.

Three things are worth knowing before using any view:

- **A report has many members.** One report can name several countries, entities and adversaries. The member views repeat the report once per member, so counting rows counts memberships, not reports. Count distinct report identifiers instead, or add up `weight_factor`, which splits each report evenly across its members and always totals 1 per report.
- **Nothing is missing, silently.** A value that the source left empty, or that could not be matched to a dimension, appears as `Unknown` with a surrogate key of `-1` and `is_unknown_member` set to true. No view returns nulls in place of a dimension label.
- **Threat groups are adversaries.** A report's threat groups are treated as adversaries, so `vw_report_group` resolves them against the adversary dimension rather than a separate group dimension. The match is made on the CTI adversary identifier alone, so a group value that is not such an identifier comes back as Unknown.

## vw_report

The starting point for anything about reports. It holds one row per RASD report with the five single-valued attributes already resolved to their labels, so classification, evidence type, importance, observation source and threat type can be filtered and grouped directly. Use it for report counts, trends over time and breakdowns by any of those attributes. The four group keys at the end are technical join keys that link a report to its countries, entities, threat groups and adversaries in the member views below.

| Column | Data Type | Description |
|---|---|---|
| id | INT | Report surrogate key. Rebuilt on every pipeline run, so do not store it elsewhere. |
| report_id | STRING | RASD report identifier. The stable key for a report. |
| title | STRING | Report title. |
| description | STRING | Report description. |
| actions | STRING | Recommended or taken actions. |
| analysis | STRING | Analyst assessment. |
| creation_date | DATE | Date the report was created. |
| publication_date | DATE | Date the report was published. |
| report_date | DATE | Report observation date. The usual date for trend analysis. |
| updated_at | TIMESTAMP | Last time the report changed in the source system. |
| classification | STRING | Report classification. |
| evidence_type | STRING | Type of supporting evidence. |
| importance | STRING | Importance level, as text rather than a number. |
| observation_source | STRING | Where the observation came from. |
| threat_type | STRING | Threat category. |
| country_group_key | STRING | Links the report to its countries in vw_report_country. |
| entity_group_key | STRING | Links the report to its entities in vw_report_entity. |
| group_group_key | STRING | Links the report to its threat groups in vw_report_group. |
| adversary_group_key | STRING | Links the report to its adversaries in vw_report_adversary. |

## vw_report_country

The countries each report concerns, one row per report and country, with the report's main attributes repeated on every row so no join back to `vw_report` is needed. Answers which places a threat touches, and supports both plain report counts per country and weighted counts that share a multi-country report fairly between them. Every report appears at least once: a report with no country gets a single Unknown row with a weight of 1.

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
| weight_factor | DECIMAL | The report's share for this country. |
| is_unknown_member | BOOLEAN | True when the country is missing or unmatched. |

## vw_report_entity

The organizations each report concerns, one row per report and entity, enriched with the entity's own attributes from the CTI register. Use it to find the most frequently targeted organizations, or to break incidents down by sector, category or entity type. Entities come in two kinds: those registered in CTI, and label-only entities whose name was read from the report text because the register held no match. Label-only entities have no sector, category or identifiers, so filter on `is_cti_entity` when those attributes matter.

| Column | Data Type | Description |
|---|---|---|
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| report_date | DATE | Report observation date. |
| classification | STRING | Report classification. |
| importance | STRING | Importance level. |
| threat_type | STRING | Threat category. |
| entity_id | BIGINT | Entity surrogate key. |
| entity_name_en | STRING | Entity name in English. Repeats the Arabic name for label-only entities. |
| entity_name_ar | STRING | Entity name in Arabic. |
| cti_id | STRING | Entity identifier in the CTI register. |
| prm_id | STRING | Entity identifier in PRM. |
| sector | STRING | Entity sector. |
| category | STRING | Entity category. |
| entity_type | STRING | Entity type. |
| entity_country | STRING | Home country of the entity, which is not the report's country. |
| is_cti_entity | BOOLEAN | True when the entity exists in the CTI register. |
| weight_factor | DECIMAL | The report's share for this entity. |
| is_unknown_member | BOOLEAN | True when the entity is missing or unmatched. |

## vw_report_group

The threat groups named in the report text, resolved against the adversary dimension. A report's threat group is itself an adversary, so each group value is matched to a CTI adversary on the adversary identifier, and only on the identifier: names are never matched. A group value that is not a CTI adversary identifier therefore resolves to Unknown, and `group_label` keeps the original text so those values stay visible and can be corrected at the source. This view answers which actors a report names itself, while `vw_report_adversary` answers which CTI adversary records point back at the report.

| Column | Data Type | Description |
|---|---|---|
| report_id | STRING | RASD report identifier. |
| title | STRING | Report title. |
| report_date | DATE | Report observation date. |
| classification | STRING | Report classification. |
| importance | STRING | Importance level. |
| threat_type | STRING | Threat category. |
| group_label | STRING | Threat group name as written in the report. |
| adversary_id | BIGINT | Adversary surrogate key the group resolved to. |
| adversary_name | STRING | Adversary name. |
| weight_factor | DECIMAL | The report's share for this group. |
| is_unknown_member | BOOLEAN | True when the report names no group, or the value is not a CTI adversary identifier. |

## vw_report_adversary

The CTI adversaries linked to each report, one row per report and adversary. The link is drawn from the CTI side: an adversary record lists the report identifiers it relates to, so this view reflects intelligence analysts' own attribution rather than anything written in the report. Reports that no adversary claims appear once with an Unknown adversary. Read it together with `vw_report_group`, which covers the group names the report itself carries.

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
| weight_factor | DECIMAL | The report's share for this adversary. |
| is_unknown_member | BOOLEAN | True when no adversary is linked to the report. |

## vw_adversary_target_country

Which countries each adversary is known to target, taken straight from CTI adversary intelligence. No reports are involved, so this view describes standing intent rather than observed incidents, and it is the right source for questions about who targets a region. Adversaries with no recorded target country do not appear at all, and unmatched countries are filtered out, which means the weights for an adversary can add up to less than 1. Note that `adversary_id` here is the CTI identifier as text, not the numeric surrogate key used in the report views.

| Column | Data Type | Description |
|---|---|---|
| adversary_id | STRING | Adversary identifier in CTI. |
| adversary_name | STRING | Adversary name. |
| country_group_key | STRING | Key of the adversary's target country set. |
| country_id | BIGINT | Country surrogate key. |
| country_name | STRING | Target country name. |
| weight_factor | DECIMAL | The adversary's share for this country. |
| is_unknown_member | BOOLEAN | Always false, because unmatched countries are excluded. |
| total_targeted_countries | BIGINT | Number of matched target countries for the adversary. |

## vw_entity_coverage

A small scorecard showing how well the entity names found in reports match the CTI entity register. It returns one row per metric rather than per report, and the metrics are raw counts, so divide them to get a coverage rate. Use it to watch data quality over time: a rising share of label-only entities or unresolved members means reports are naming organizations the register does not hold yet.

| Column | Data Type | Description |
|---|---|---|
| metric | STRING | Metric name. |
| value | BIGINT | Metric value. |

The metrics returned are `cti_entities`, the number of registered CTI entities; `cti_entities_with_prm_id`, how many of those also carry a PRM identifier; `label_only_entities`, entities known only from report text; `unresolved_report_members`, entity sets holding at least one name that could not be matched; and `reports_with_no_known_entity`, reports carrying at least one unmatched entity.
