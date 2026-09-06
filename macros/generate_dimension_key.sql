{#
  Macro for generating surrogate keys for dimension tables
  Uses ROW_NUMBER() OVER() for cross-engine compatibility
#}

{% macro generate_dimension_key(order_by_column) %}
  {%- set engine = target.type | lower -%}
  
  {%- if engine == 'postgres' -%}
    -- PostgreSQL: Use BIGINT with identity for production, row_number for dev
    ROW_NUMBER() OVER (ORDER BY {{ order_by_column }})::BIGINT
    
  {%- elif engine == 'spark' -%}
    -- Spark: Use row_number() 
    CAST(ROW_NUMBER() OVER (ORDER BY {{ order_by_column }}) AS BIGINT)
    
  {%- elif engine == 'trino' -%}
    -- Trino: Use row_number()
    CAST(ROW_NUMBER() OVER (ORDER BY {{ order_by_column }}) AS BIGINT)
    
  {%- else -%}
    -- Default: Use row_number()
    CAST(ROW_NUMBER() OVER (ORDER BY {{ order_by_column }}) AS BIGINT)
    
  {%- endif -%}
{% endmacro %}