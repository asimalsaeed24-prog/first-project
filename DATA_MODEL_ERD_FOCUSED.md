# CTI/RASD Data Model - Focused ERD Documentation

This document provides a focused overview of the CTI/RASD data model with:
1. **Table descriptions with columns and data types**
2. **ERD diagram using Mermaid flowchart TD**
3. **Semantic layer view descriptions and purpose**

---

## 1. Table Descriptions with Columns & Data Types

Complete table descriptions with all columns, data types, and descriptions.

---

## 2. ERD Diagram - Complete Data Model

```mermaid
flowchart TD
    %% Source Systems
    CTI[CTI Source System<br/>adversary, entities]
    RASD[RASD Source System<br/>rasd reports]
    
    %% Staging Layer
    STG_ADV[stg_adversary]
    STG_ENT[stg_entity]
    STG_REP[stg_report]
    
    %% Core Dimension Tables
    DIM_KEY[dim_key<br/>Central Key Registry]
    
    %% Dimension Categories
    RASD_DIMS[RASD Dimensions<br/>dim_rasd_classification<br/>dim_rasd_evidence_type<br/>dim_rasd_importance_level<br/>dim_rasd_source<br/>dim_rasd_threat_type<br/>dim_rasd_group<br/>dim_rasd_entity]
    
    CTI_DIMS[CTI Dimensions<br/>dim_cti_adversary]
    
    SHARED_DIMS[Shared Dimensions<br/>dim_country]
    
    %% Fact Table
    FACT[fact_rasd_report<br/>Central Fact Table]
    
    %% Bridge Tables
    BRIDGE_COUNTRY[bridge_country]
    BRIDGE_ENTITY[bridge_entity]
    BRIDGE_GROUP[bridge_group]
    BRIDGE_ADV[bridge_adversary]
    BRIDGE_ADV_COUNTRY[bridge_adversary_country]
    
    %% Semantic Views
    VW_REPORT[vw_report]
    VW_REPORT_COUNTRY[vw_report_country]
    VW_REPORT_ENTITY[vw_report_entity]
    VW_REPORT_GROUP[vw_report_group]
    VW_REPORT_ADV[vw_report_adversary]
    VW_ADV_COUNTRY[vw_adversary_target_country]
    VW_COVERAGE[vw_entity_coverage]
    
    %% Data Flow
    CTI --> STG_ADV
    CTI --> STG_ENT
    RASD --> STG_REP
    
    STG_ADV --> DIM_KEY
    STG_ENT --> DIM_KEY
    STG_REP --> DIM_KEY
    
    DIM_KEY --> RASD_DIMS
    DIM_KEY --> CTI_DIMS
    DIM_KEY --> SHARED_DIMS
    
    STG_REP --> FACT
    RASD_DIMS --> FACT
    CTI_DIMS --> FACT
    
    FACT --> BRIDGE_COUNTRY
    FACT --> BRIDGE_ENTITY
    FACT --> BRIDGE_GROUP
    FACT --> BRIDGE_ADV
    
    SHARED_DIMS --> BRIDGE_COUNTRY
    RASD_DIMS --> BRIDGE_ENTITY
    RASD_DIMS --> BRIDGE_GROUP
    CTI_DIMS --> BRIDGE_ADV
    
    STG_ADV --> BRIDGE_ADV_COUNTRY
    CTI_DIMS --> BRIDGE_ADV_COUNTRY
    SHARED_DIMS --> BRIDGE_ADV_COUNTRY
    
    FACT --> VW_REPORT
    BRIDGE_COUNTRY --> VW_REPORT_COUNTRY
    BRIDGE_ENTITY --> VW_REPORT_ENTITY
    BRIDGE_GROUP --> VW_REPORT_GROUP
    BRIDGE_ADV --> VW_REPORT_ADV
    BRIDGE_ADV_COUNTRY --> VW_ADV_COUNTRY
    RASD_DIMS --> VW_COVERAGE
    
    %% Style
    classDef source fill:#e1f5fe,stroke:#01579b
    classDef staging fill:#f3e5f5,stroke:#4a148c
    classDef dim fill:#e8f5e8,stroke:#1b5e20
    classDef fact fill:#fff3e0,stroke:#e65100
    classDef bridge fill:#fce4ec,stroke:#880e4f
    classDef semantic fill:#e0f2f1,stroke:#004d40
    
    class CTI,RASD source
    class STG_ADV,STG_ENT,STG_REP staging
    class DIM_KEY,RASD_DIMS,CTI_DIMS,SHARED_DIMS dim
    class FACT fact
    class BRIDGE_COUNTRY,BRIDGE_ENTITY,BRIDGE_GROUP,BRIDGE_ADV,BRIDGE_ADV_COUNTRY bridge
    class VW_REPORT,VW_REPORT_COUNTRY,VW_REPORT_ENTITY,VW_REPORT_GROUP,VW_REPORT_ADV,VW_ADV_COUNTRY,VW_COVERAGE semantic
```

---

## 3. Semantic Layer View Descriptions & Purpose

Detailed descriptions of all semantic views with their business purposes and use cases.