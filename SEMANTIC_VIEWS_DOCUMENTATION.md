# CTI/RASD Semantic Views Documentation

## Core View

### `vw_report`
**Description**: Main report view with all dimension attributes denormalized for easy reporting.

**Schema**:
| Field | Data Type | Description |
|-------|-----------|-------------|
| `id` | BIGINT | Surrogate key (row_number) |
| `report_id` | TEXT | Unique report identifier |
| `title` | TEXT | Report title |
| `description` | TEXT | Report description |
| `actions` | TEXT | Actions taken |
| `analysis` | TEXT | Analysis content |
| `creation_date` | DATE | Report creation date |
| `publication_date` | DATE | Report publication date |
| `report_date` | DATE | Report date |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `classification` | TEXT | Classification name  |
| `evidence_type` | TEXT | Type of evidence  |
| `importance` | TEXT | Importance level  |
| `observation_source` | TEXT | Source of observation |
| `threat_type` | TEXT | Type of threat |
| `country_group_key` | VARCHAR(32) | Hash key for country grouping |
| `entity_group_key` | VARCHAR(32) | Hash key for entity grouping |
| `group_group_key` | VARCHAR(32) | Hash key for threat group grouping |
| `adversary_group_key` | VARCHAR(32) | Hash key for adversary grouping |

**Purpose**: Provides a complete view of all reports with denormalized dimension attributes for easy querying.

## Member Relationship Views

### `vw_report_country`
**Description**: Links reports to their associated countries with weight distribution.

**Schema**:
| Field | Data Type | Description |
|-------|-----------|-------------|
| `report_id` | TEXT | Report identifier |
| `title` | TEXT | Report title |
| `report_date` | DATE | Report date |
| `classification` | TEXT | Classification name |
| `importance` | TEXT | Importance level |
| `threat_type` | TEXT | Threat type |
| `country_id` | BIGINT | Country dimension ID |
| `country_name` | TEXT | Country name |
| `weight_factor` | FLOAT | Proportional weight (1/number of countries in report) |
| `is_unknown_member` | BOOLEAN | True if country is unknown/unresolved |

**Purpose**: Shows which countries are associated with each report and their proportional weight.

### `vw_report_entity`
**Description**: Links reports to their associated entities (organizations) with detailed entity information.

**Schema**:
| Field | Data Type | Description |
|-------|-----------|-------------|
| `report_id` | TEXT | Report identifier |
| `title` | TEXT | Report title |
| `report_date` | DATE | Report date |
| `classification` | TEXT | Classification name |
| `importance` | TEXT | Importance level |
| `threat_type` | TEXT | Threat type |
| `entity_id` | BIGINT | Entity dimension ID |
| `entity_name_en` | TEXT | Entity name (English) |
| `entity_name_ar` | TEXT | Entity name (Arabic) |
| `cti_id` | TEXT | CTI system identifier |
| `prm_id` | TEXT | PRM system identifier |
| `sector` | TEXT | Entity sector  |
| `category` | TEXT | Entity category |
| `entity_type` | TEXT | Type of entity |
| `entity_country` | TEXT | Entity's country |
| `is_cti_entity` | BOOLEAN | True if entity is from CTI system |
| `weight_factor` | FLOAT | Proportional weight (1/number of entities in report) |
| `is_unknown_member` | BOOLEAN | True if entity is unknown/unresolved |

**Purpose**: Shows which entities (organizations) are associated with each report with detailed entity attributes.

### `vw_report_group`
**Description**: Links reports to their associated threat groups.

**Schema**:
| Field | Data Type | Description |
|-------|-----------|-------------|
| `report_id` | TEXT | Report identifier |
| `title` | TEXT | Report title |
| `report_date` | DATE | Report date |
| `classification` | TEXT | Classification name |
| `importance` | TEXT | Importance level |
| `threat_type` | TEXT | Threat type |
| `group_id` | BIGINT | Group dimension ID |
| `group_name` | TEXT | Threat group name |
| `weight_factor` | FLOAT | Proportional weight (1/number of groups in report) |
| `is_unknown_member` | BOOLEAN | True if group is unknown/unresolved |

**Purpose**: Shows which threat groups are associated with each report.

### `vw_report_adversary`
**Description**: Links reports to their associated adversaries (CTI-specific).

**Schema**:
| Field | Data Type | Description |
|-------|-----------|-------------|
| `report_id` | TEXT | Report identifier |
| `title` | TEXT | Report title |
| `report_date` | DATE | Report date |
| `classification` | TEXT | Classification name |
| `importance` | TEXT | Importance level |
| `threat_type` | TEXT | Threat type |
| `adversary_id` | BIGINT | Adversary dimension ID |
| `adversary_name` | TEXT | Adversary name |
| `weight_factor` | FLOAT | Proportional weight (1/number of adversaries in report) |
| `is_unknown_member` | BOOLEAN | True if adversary is unknown/unresolved |

**Purpose**: Shows which adversaries (from CTI system) are associated with each report.

### `vw_adversary_target_country`
**Description**: Shows direct relationships between adversaries and the countries they target, based on CTI adversary data.

**Schema**:
| Field | Data Type | Description |
|-------|-----------|-------------|
| `adversary_id` | TEXT | Adversary natural key from CTI |
| `adversary_name` | TEXT | Adversary name |
| `country_group_key` | VARCHAR(32) | Hash key of sorted target countries for this adversary |
| `country_id` | BIGINT | Country dimension ID |
| `country_name` | TEXT | Country name |
| `weight_factor` | FLOAT | Proportional weight (1/number of countries targeted by adversary) |
| `is_unknown_member` | BOOLEAN | True if country is unknown/unresolved |
| `total_targeted_countries` | BIGINT | Total number of countries targeted by this adversary |

**Purpose**: Provides direct adversary-country targeting relationships from CTI intelligence data, showing which adversaries are known to target which countries.


