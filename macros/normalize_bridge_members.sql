{#
  The member array behind a bridge key: split, trim, upper, dedupe, sort.

  This is the exact array that generate_bridge_key hashes, exposed on its own so
  a bridge model can explode it. Keeping both sides on this one macro is what
  guarantees a fact's group key and its bridge rows describe the same set.

  A report with no values collapses to a single 'UNKNOWN' member, which resolves
  to the dimension's id = -1 row.
#}

{% macro normalize_bridge_members(column_name, delimiter=',', to_upper=true, unknown_value='UNKNOWN') %}
  {%- set engine = target.type | lower -%}
  {%- set token = 'upper(trim(x))' if to_upper else 'trim(x)' -%}

  {%- if engine == 'trino' -%}
    {%- set tokens = "filter(transform(split(coalesce(" ~ column_name ~ ", ''), '" ~ delimiter ~ "'), x -> " ~ token ~ "), x -> x <> '')" -%}
    CASE
      WHEN cardinality({{ tokens }}) = 0 THEN ARRAY['{{ unknown_value }}']
      ELSE array_sort(array_distinct({{ tokens }}))
    END

  {%- elif engine == 'spark' or engine == 'databricks' -%}
    {#- Spark's split() takes a REGEX, so quote the delimiter: '|' would
        otherwise match the empty string and shatter every character. -#}
    {%- set tokens = "filter(transform(split(coalesce(" ~ column_name ~ ", ''), '\\\\Q" ~ delimiter ~ "\\\\E'), x -> " ~ token ~ "), x -> x <> '')" -%}
    CASE
      WHEN size({{ tokens }}) = 0 THEN array('{{ unknown_value }}')
      ELSE array_sort(array_distinct({{ tokens }}))
    END

  {%- else -%}
    {{ exceptions.raise_compiler_error("normalize_bridge_members does not support engine: " ~ engine) }}

  {%- endif -%}
{% endmacro %}


{#
  Engine-appropriate FROM-clause explode of an array column.
  Trino:  CROSS JOIN UNNEST(arr) AS t(member_token)
  Spark:  LATERAL VIEW explode(arr) t AS member_token
#}
{% macro explode_array(array_expression, table_alias='t', column_alias='member_token') %}
  {%- set engine = target.type | lower -%}

  {%- if engine == 'trino' -%}
    CROSS JOIN UNNEST({{ array_expression }}) AS {{ table_alias }}({{ column_alias }})
  {%- elif engine == 'spark' or engine == 'databricks' -%}
    LATERAL VIEW explode({{ array_expression }}) {{ table_alias }} AS {{ column_alias }}
  {%- else -%}
    {{ exceptions.raise_compiler_error("explode_array does not support engine: " ~ engine) }}
  {%- endif -%}
{% endmacro %}
