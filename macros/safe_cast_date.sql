{#
  Best-effort parse of a string date column.

  Every date column in cti.rasd is typed as string, so each candidate format is
  tried in order and the column is NULL when none of them match -- never an
  error. Trino uses MySQL-style patterns (date_parse), Spark uses Java ones,
  so the default list is per engine.

  dd/MM is preferred over MM/dd; swap the two entries if the source is US
  formatted.
#}

{% macro safe_cast_date(column_name, as_timestamp=false) %}
  {%- set engine = target.type | lower -%}
  {%- set cleaned = "NULLIF(TRIM(" ~ column_name ~ "), '')" -%}

  {%- if engine == 'trino' -%}
    {%- set formats = ['%Y-%m-%d %H:%i:%s', '%Y-%m-%dT%H:%i:%s', '%Y-%m-%d', '%d/%m/%Y %H:%i:%s', '%d/%m/%Y', '%m/%d/%Y'] -%}
    CAST(
      COALESCE(
        TRY(CAST({{ cleaned }} AS TIMESTAMP)),
        {%- for format in formats %}
        TRY(date_parse({{ cleaned }}, '{{ format | replace("'", "''") }}')){% if not loop.last %},{% endif %}
        {%- endfor %}
      ) AS {{ 'TIMESTAMP' if as_timestamp else 'DATE' }}
    )

  {%- elif engine == 'spark' or engine == 'databricks' -%}
    {%- set formats = ["yyyy-MM-dd'T'HH:mm:ss.SSSXXX", "yyyy-MM-dd'T'HH:mm:ss", 'yyyy-MM-dd HH:mm:ss', 'yyyy-MM-dd', 'dd/MM/yyyy HH:mm:ss', 'dd/MM/yyyy', 'MM/dd/yyyy'] -%}
    CAST(
      COALESCE(
        {%- for format in formats %}
        TRY_TO_TIMESTAMP({{ cleaned }}, '{{ format | replace("'", "''") }}'){% if not loop.last %},{% endif %}
        {%- endfor %}
      ) AS {{ 'TIMESTAMP' if as_timestamp else 'DATE' }}
    )

  {%- else -%}
    {{ exceptions.raise_compiler_error("safe_cast_date does not support engine: " ~ engine) }}

  {%- endif -%}
{% endmacro %}
