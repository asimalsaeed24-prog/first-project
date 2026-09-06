{#
  Macro to create surrogate key columns for dimension tables
  Handles different database engines appropriately
#}

{% macro create_dimension_pk() %}
  {%- set engine = target.type | lower -%}
  
  {%- if engine == 'postgres' -%}
    -- PostgreSQL: Use BIGSERIAL for larger range
    id BIGSERIAL PRIMARY KEY
    
  {%- elif engine == 'spark' -%}
    -- Spark: Use BIGINT with row_number() in the model SQL
    -- This macro returns the column definition, actual population happens in model
    id BIGINT
    
  {%- elif engine == 'trino' -%}
    -- Trino: Use BIGINT
    id BIGINT
    
  {%- else -%}
    -- Default: Use BIGINT
    id BIGINT
    
  {%- endif -%}
{% endmacro %}