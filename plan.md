# CTI/RASD Data Model Enhancement Plan

## Overview
This plan outlines the steps to enhance the CTI/RASD data model by:
1. Creating a complete dimension table for adversaries
2. Integrating adversary country data into the existing country dimension
3. Creating a bridge table between adversaries and reports
4. Fixing naming inconsistencies between dimension files and SQL references

## Current State Analysis

### Existing Files:
- `sql/staging/stg_adversary.sql`: Contains adversary data with country information
- `sql/dim/dim_cti_adversary.sql`: Empty file (needs implementation)
- `sql/bridge/bridge_adversary.sql`: Incomplete (only selects adversary_id)
- `sql/keys/dim_key.sql`: Already includes `dim_cti_adversary` in key generation

### Naming Convention Clarification:
- **RASD-specific dimensions**: Should use `dim_rasd_` prefix in SQL references
- **Shared dimensions**: `dim_country` (shared between CTI and RASD)
- **CTI-specific dimensions**: `dim_cti_adversary` (CTI-specific)
- **Current Issue**: Some SQL references use `dim_` instead of `dim_rasd_` for RASD dimensions

## Tasks Breakdown

### Task 1: Fix Naming Inconsistencies (Update SQL References)

#### 1.1 Identify Current SQL References to Fix:
- `dim_classification` → `dim_rasd_classification`
- `dim_evidence_type` → `dim_rasd_evidence_type`
- `dim_importance_level` → `dim_rasd_importance_level`
- `dim_source` → `dim_rasd_source`
- `dim_group` → `dim_rasd_group`
- `dim_entity` → `dim_rasd_entity`
- `dim_threat_type` → `dim_rasd_threat_type`
- `dim_country` → **Keep as is** (shared dimension)
- `dim_cti_adversary` → **Keep as is** (CTI-specific)

#### 1.2 Update All SQL References:
- Update JOIN clauses in: fact_report.sql, all bridge tables, all semantic views
- Update WHERE clauses in dimension files referencing dim_key table
- Update table references throughout the codebase

#### 1.3 File Names Remain Unchanged:
- Keep existing file names: `dim_rasd_*.sql`
- Only update SQL references within files

### Task 2: Create Complete dim_cti_adversary.sql

#### 2.1 File Structure:
- Follow pattern from `dim_rasd_entity.sql`
- Include "Unknown" record with ID = -1
- Join with `dim_key` table using `dim_cti_adversary` dimension
- Include fields: id, adversary_id, adversary_name

#### 2.2 Source Data:
- Use `{{ target_schema }}.stg_adversary` as source
- Join with `{{ target_schema }}.dim_key` on adversary_id

### Task 3: Integrate Adversary Country Data into dim_country

#### 3.1 Update dim_key.sql:
- Add country data from `stg_adversary.country_members` to existing country dimension
- Use `LATERAL VIEW explode` to extract individual country values
- Use dimension name `dim_country` (shared dimension)

#### 3.2 Update dim_country.sql:
- No changes needed (already reads from dim_key with `dim_country` dimension)
- Country data from both reports and adversaries will be available

### Task 4: Create Complete bridge_adversary.sql

#### 4.1 Requirements:
- Connect `dim_cti_adversary` to `fact_report`
- Handle many-to-many relationship between adversaries and reports
- Include weight_factor for proportional attribution
- Follow pattern from existing bridge tables (country, entity, group)

#### 4.2 Design:
- Source: `stg_adversary.members_rasd_reports` (array of RASD report IDs)
- Bridge between adversary_id and report_id
- Include: adversary_group_key, adversary_id, report_id, weight_factor, is_unknown_member

### Task 5: Update fact_report.sql (if needed)

#### 5.1 Check if adversary relationship should be added:
- Currently fact_report has: country_group_key, entity_group_key, group_group_key
- May need to add: adversary_group_key if direct relationship needed

## Implementation Order

1. **First**: Fix naming inconsistencies (Task 1)
   - Update SQL references to use `dim_rasd_` prefix for RASD dimensions
   - Keep `dim_country` and `dim_cti_adversary` as is

2. **Second**: Create dim_cti_adversary.sql (Task 2)

3. **Third**: Update country integration in dim_key.sql (Task 3)

4. **Fourth**: Create bridge_adversary.sql (Task 4)

5. **Fifth**: Verify fact_report.sql and update if needed (Task 5)

## Validation Steps

After implementation, verify:
1. All SQL references use correct naming convention:
   - RASD dimensions: `dim_rasd_*`
   - Shared dimension: `dim_country`
   - CTI dimension: `dim_cti_adversary`
2. dim_key.sql generates keys for all dimensions correctly
3. All SQL queries compile without reference errors
4. Bridge tables properly connect dimensions to facts
5. Adversary country data appears in dim_country
6. The Airflow DAG can run the complete pipeline

## Risks and Considerations

1. **Consistency**: Ensure all references follow the new naming convention
2. **Data Integration**: Country data from adversaries must integrate properly with existing country data
3. **Relationship Mapping**: Bridge table must correctly map adversaries to reports
4. **Testing**: Comprehensive testing needed to verify all relationships

## Success Criteria

1. All SQL references use consistent naming:
   - RASD: `dim_rasd_*`
   - Shared: `dim_country`
   - CTI: `dim_cti_adversary`
2. `dim_cti_adversary` is fully functional and follows dimension patterns
3. Adversary country data is integrated into `dim_country`
4. `bridge_adversary` properly connects adversaries to reports
5. Complete pipeline runs without naming reference errors