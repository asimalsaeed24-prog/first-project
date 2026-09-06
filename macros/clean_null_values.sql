{#
  Macro for cleaning NULL values and empty strings across different SQL engines
  Handles common NULL representations like 'NULL', 'NUL', '', etc.
#}

{% macro clean_null_values(column_name, null_values=['NULL', 'NUL', 'null', 'nul', '']) %}
  {%- set engine = target.type | lower -%}
  
  -- Build the CASE statement dynamically
  CASE
    {%- for null_val in null_values %}
    WHEN UPPER({{ column_name }}) = UPPER('{{ null_val }}') THEN NULL
    {%- endfor %}
    WHEN {{ column_name }} IS NULL THEN NULL
    ELSE TRIM({{ column_name }})
  END
  
{% endmacro %}