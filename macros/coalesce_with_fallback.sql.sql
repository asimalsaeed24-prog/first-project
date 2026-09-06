{#
  Macro for COALESCE with intelligent fallback logic
  Returns first non-NULL, non-empty value from the list
#}

{% macro coalesce_with_fallback(column_list, default_value='') %}
  {%- set engine = target.type | lower -%}
  
  {%- if engine == 'postgres' or engine == 'trino' -%}
    -- PostgreSQL and Trino: Use COALESCE
    COALESCE(
      {%- for column in column_list %}
      NULLIF(TRIM({{ column }}), ''),
      {%- endfor %}
      '{{ default_value }}'
    )
    
  {%- elif engine == 'spark' -%}
    -- Spark: Use coalesce
    coalesce(
      {%- for column in column_list %}
      nullif(trim({{ column }}), ''),
      {%- endfor %}
      '{{ default_value }}'
    )
    
  {%- else -%}
    -- Default: Use COALESCE
    COALESCE(
      {%- for column in column_list %}
      NULLIF(TRIM({{ column }}), ''),
      {%- endfor %}
      '{{ default_value }}'
    )
    
  {%- endif -%}
{% endmacro %}