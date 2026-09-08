-- One row per threat group ever seen on a RASD report.
--
-- The id comes from dim_key and never changes -- see sql/keys/dim_key.sql. This
-- table itself holds no state and can be dropped and rebuilt at any time.
--
-- A threat group that disappears from the source keeps its row, because dim_key keeps
-- its key, so a report built before it vanished still resolves its id to a name.

SELECT
  CAST(-1 AS BIGINT) AS id,
  'Unknown' AS group_name

UNION ALL

SELECT
  id,
  label AS group_name
FROM {{ target_schema }}.dim_key
WHERE dimension = 'dim_group'
