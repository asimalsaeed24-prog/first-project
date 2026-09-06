{#
  Macro for multi-valued dimension group keys
  Splits a delimited column, normalizes it (trim, upper, dedupe, sort),
  and hashes it into a stable group key for bridge tables.

  Sorting makes 'US,SA' and 'SA,US' produce the same key.
  lower() makes Trino and Spark produce the same key.
#}

{% macro generate_bridge_key(column_name, delimiter=',', to_upper=true, unknown_value='UNKNOWN', separator='|') %}
  {%- set engine = target.type | lower -%}
  {%- set token = 'upper(trim(x))' if to_upper else 'trim(x)' -%}

  {%- if engine == 'trino' -%}
    -- Trino: cardinality / ARRAY[] / to_hex(md5(to_utf8()))
    lower(to_hex(md5(to_utf8(array_join(
      CASE
        WHEN cardinality(filter(transform(split(coalesce({{ column_name }}, ''), '{{ delimiter }}'), x -> {{ token }}), x -> x <> '')) = 0
        THEN ARRAY['{{ unknown_value }}']
        ELSE array_sort(array_distinct(filter(transform(split(coalesce({{ column_name }}, ''), '{{ delimiter }}'), x -> {{ token }}), x -> x <> '')))
      END,
      '{{ separator }}'
    )))))

  {%- elif engine == 'spark' or engine == 'databricks' -%}
    -- Spark: size / array() / md5() returns hex directly
    lower(md5(array_join(
      CASE
        WHEN size(filter(transform(split(coalesce({{ column_name }}, ''), '{{ delimiter }}'), x -> {{ token }}), x -> x <> '')) = 0
        THEN array('{{ unknown_value }}')
        ELSE array_sort(array_distinct(filter(transform(split(coalesce({{ column_name }}, ''), '{{ delimiter }}'), x -> {{ token }}), x -> x <> '')))
      END,
      '{{ separator }}'
    )))

  {%- else -%}
    {{ exceptions.raise_compiler_error("generate_bridge_key does not support engine: " ~ engine) }}

  {%- endif -%}
{% endmacro %}