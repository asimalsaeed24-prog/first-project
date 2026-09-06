{#
  Macro for generating hash keys from multiple columns
  Uses CONCAT with "#" for NULL values, then creates MD5 hash
#}

{% macro generate_hash_key(column_list, separator='|') %}
  {%- set engine = target.type | lower -%}
  
  {%- if engine == 'postgres' -%}
    -- PostgreSQL: Use MD5 on concatenated string
    MD5(
      CONCAT_WS('{{ separator }}',
        {%- for column in column_list %}
        COALESCE({{ column }}::TEXT, '#'){% if not loop.last %},{% endif %}
        {%- endfor %}
      )
    )
    
  {%- elif engine == 'spark' -%}
    -- Spark: Use MD5 on concatenated string
    MD5(
      CONCAT_WS('{{ separator }}',
        {%- for column in column_list %}
        COALESCE(CAST({{ column }} AS STRING), '#'){% if not loop.last %},{% endif %}
        {%- endfor %}
      )
    )
    
  {%- elif engine == 'trino' -%}
    -- Trino: Use MD5 on concatenated string
    MD5(
      ARRAY_JOIN(
        ARRAY[
          {%- for column in column_list %}
          COALESCE(CAST({{ column }} AS VARCHAR), '#'){% if not loop.last %},{% endif %}
          {%- endfor %}
        ],
        '{{ separator }}'
      )
    )
    
  {%- else -%}
    -- Default: Use MD5 on concatenated string
    MD5(
      CONCAT_WS('{{ separator }}',
        {%- for column in column_list %}
        COALESCE(CAST({{ column }} AS VARCHAR), '#'){% if not loop.last %},{% endif %}
        {%- endfor %}
      )
    )
    
  {%- endif -%}
{% endmacro %}