{#
  Macro for multi-valued dimension group keys.

  Hashes the normalized member set (see normalize_bridge_members) into a stable
  group key. Reports naming the same set -- in any order, any casing -- share a
  key, so the bridge stores one row per distinct set rather than per report.

  Both this and the bridge models build their members through the one macro, so
  a fact's key and its bridge rows can never describe different sets.
  lower() makes Trino and Spark agree on the hex digest.
#}

{% macro generate_bridge_key(column_name, delimiter=',', to_upper=true, unknown_value='UNKNOWN', separator='|') %}
  {%- set engine = target.type | lower -%}
  {%- set members = normalize_bridge_members(column_name, delimiter, to_upper, unknown_value) -%}

  {%- if engine == 'trino' -%}
    -- Trino: md5() takes/returns varbinary
    lower(to_hex(md5(to_utf8(array_join({{ members }}, '{{ separator }}')))))

  {%- elif engine == 'spark' or engine == 'databricks' -%}
    -- Spark: md5() returns hex directly
    lower(md5(array_join({{ members }}, '{{ separator }}')))

  {%- else -%}
    {{ exceptions.raise_compiler_error("generate_bridge_key does not support engine: " ~ engine) }}

  {%- endif -%}
{% endmacro %}
