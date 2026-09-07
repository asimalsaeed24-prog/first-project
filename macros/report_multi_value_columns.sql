{#
  The multi-valued columns of cti.rasd, defined once.

  fact_report hashes these into group keys and the bridge models explode the
  same expressions; if the two ever drifted apart a fact would point at a group
  whose membership was derived from different text.
#}

{% macro report_country_source() %}country{% endmacro %}

{% macro report_group_source() %}related_groups{% endmacro %}


{#
  A report is described by the strongest entity identifier it carries, falling
  back to the free-text labels only when it has no identifier at all.

  entities_rasd_id has no counterpart in cti.entities, so those tokens resolve
  to the Unknown member (id = -1) rather than vanishing -- bridge_entity's
  is_unknown_member counts exactly that cohort.
#}
{% macro report_entity_source() -%}
  COALESCE(NULLIF(TRIM(entities_cti_id), ''), NULLIF(TRIM(entities_prm_id), ''), NULLIF(TRIM(entities_rasd_id), ''), NULLIF(TRIM(entities_names_ar), ''))
{%- endmacro %}
