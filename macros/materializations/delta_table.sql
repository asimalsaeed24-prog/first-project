-- macros/materializations/delta_table.sql
{% materialization delta_table, default %}
  {%- set identifier = model['alias'] or model['name'] -%}
  {%- set target_relation = api.Relation.create(
        database=database, 
        schema=schema, 
        identifier=identifier, 
        type='table'
  ) -%}
  
  {% call statement('main') -%}
    CREATE OR REPLACE TABLE {{ target_relation }}
    AS {{ sql }}
  {%- endcall %}
  
  {{ return({'relations': [target_relation]}) }}
{% endmaterialization %}