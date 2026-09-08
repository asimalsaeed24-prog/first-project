# CTI/RASD star schema

A star schema over the raw CTI/RASD report feed, available two ways:

| | |
| --- | --- |
| [`sql/`](sql) + [`run.py`](run.py) | plain Spark SQL models, executed with `spark.sql` |
| [`load_postgres.py`](load_postgres.py) | ships the finished star schema to Postgres |
| [`sql/semantic/`](sql/semantic) | business-facing views over the star schema |
| [`dags/`](dags) | Airflow, one DAG, one task per model |
| [`django_warehouse/`](django_warehouse) | Django models and migrations owning the Postgres schema |
| [`models/`](models) + [`macros/`](macros) | the dbt project (Trino and Spark) |

Both produce the same tables. The SQL models are the ones to reach for when you
want to run, read or debug a query directly.

## Running it

`run.py` builds **one model**:

```bash
spark-submit run.py dim/dim_country
```

It reads that one `.sql` file, swaps in the schema names, and writes it
according to the folder it came from:

| folder | becomes | how |
| --- | --- | --- |
| `keys/` | a table | append-only, never overwritten |
| `semantic/` | a **view** | `CREATE OR REPLACE VIEW` |
| everything else | a table | created once, then `INSERT OVERWRITE` |

The order the models go in is **not** in this script — it lives in `PIPELINE`
in the DAG. One model per run means each is its own Airflow task: visible in the
graph by name, retryable on its own, and self-identifying when it fails.

Statements are split on `;`, so a `;` must not appear inside a string literal or
a comment in any `.sql` file.

`INSERT OVERWRITE` requires the query's columns to match the existing table, so
if you add or rename a column in a model, `DROP` its table once and let the
script recreate it. That is safe for every table except `dim_key`.


## Keys are stable — do not drop `dim_key`

**`gold.dim_key` is the only table in the warehouse that holds state. Back it
up. Dropping it re-mints every id the business reports against.** Every other
table, dimensions included, is derived and can be rebuilt at any time.

One row per (dimension, value):

| dimension | natural_key | label | id | first_seen_at |
| --- | --- | --- | --- | --- |
| dim_country | `SAUDI ARABIA` | `Saudi Arabia` | 1 | 2026-09-08 … |
| dim_country | `QATAR` | `Qatar` | 2 | 2026-09-08 … |
| dim_source | `OSINT` | `OSINT` | 1 | 2026-09-08 … |

Ids start at 1 and are unique **within** a dimension. Each run appends only
values the table has never seen, numbering them from that dimension's current
maximum:

```sql
coalesce(high_water.max_id, 0)
  + row_number() OVER (PARTITION BY unseen.dimension ORDER BY unseen.natural_key) AS id
```

Nothing already in the table is ever updated or deleted, so an existing value
keeps its id no matter what arrives later. Previously each dimension minted its
own id with `row_number()` over an alphabetical sort, so a new label inserted
mid-alphabet moved every id after it.

The dimensions then just read their slice of it, which is why they are only a
few lines each:

```sql
SELECT CAST(-1 AS BIGINT) AS id, 'Unknown' AS country_name
UNION ALL
SELECT id, label AS country_name
FROM gold.dim_key
WHERE dimension = 'dim_country';
```

Notes on the behaviour:

- **To add a dimension**, add a branch to the `candidates` UNION in
  [dim_key.sql](sql/keys/dim_key.sql). Nothing else needs to change.
- Values are matched case-insensitively on `natural_key`. Two spellings of one
  value settle on a single deterministic `label` rather than flip-flopping.
- A value that disappears from the source **keeps its key**, so a report built
  before it vanished still resolves its id to a name — and if it comes back it
  gets its original id.
- `dim_entity` is keyed on `cti_id` where the entity has one, so a client
  renaming itself keeps its key. Its attributes are read fresh from
  `stg_entity` every run, so they stay current while the id stays fixed.
- The `id = -1` 'Unknown' row is not in `dim_key`. Each dimension unions it in,
  so `fact_report` never carries a NULL foreign key.

## Airflow

One DAG, [dags/cti_pipeline_dag.py](dags/cti_pipeline_dag.py), covering the lot:
build the star schema, migrate the Postgres schema with Django, then move the
data across. One task per model throughout — 33 tasks in 10 groups.

The whole schedule is one array:

```python
PIPELINE = [
    # group name                kind      models or layers
    ("staging_tables",          BUILD,    ["staging"]),
    ("key_registry",            BUILD,    ["keys"]),
    ("dimension_tables",        BUILD,    ["dim"]),
    ("fact_and_bridge_tables",  BUILD,    ["bridge", "fact"]),
    ("semantic_spine",          BUILD,    ["semantic/vw_report"]),
    ("semantic_views",          BUILD,    ["semantic/vw_report_country",
                                           "semantic/vw_report_entity",
                                           "semantic/vw_report_group"]),
    ("semantic_metrics",        BUILD,    ["semantic"]),
    ("django_migrate",          MIGRATE,  []),
    ("postgres_dimensions",     LOAD,     ["dim"]),
    ("postgres_facts",          LOAD,     ["bridge", "fact"]),
]
```

Each entry is one **task group**. Groups run one after another, everything
inside a group runs in parallel. `staging_tables` holds `stg_report` and
`stg_entity`, `dimension_tables` holds the eight dimensions, and so on:

```
staging_tables (2) -> key_registry (1) -> dimension_tables (8)
  -> fact_and_bridge_tables (4) -> semantic_spine (1) -> semantic_views (3)
  -> semantic_metrics (1) -> django_migrate (1)
  -> postgres_dimensions (8) -> postgres_facts (4)
```

The `kind` column decides what the group builds: `BUILD` is
`spark-submit run.py <model>`, `LOAD` is `spark-submit load_postgres.py <table>`,
`MIGRATE` is `manage.py migrate`.

A models entry is either **a layer** — `"dim"` expands to every `.sql` file in
`sql/dim/`, so adding a model adds a task with no DAG edit — or **one model**,
`"semantic/vw_report"`, pinning something that has to go first.

A model already scheduled by an earlier group is skipped later, *within its
phase*. That lets `semantic_spine` pin the view the others build on and
`semantic_metrics` sweep up everything else in the folder. It is per-phase on
purpose: otherwise the Postgres groups would find their tables already claimed
by the build groups and come out empty.

Reorder the array, split a group, or pin a model, and the graph follows —
nothing below the list changes.

`bridge` and `fact` share a group because both read staging and the dimensions,
and neither reads the other. `max_active_runs=1` is deliberate: `dim_key` is
appended to, and two overlapping runs could mint the same id twice.


### Configuration

The DAG owns every setting. [dags/cti_config.py](dags/cti_config.py) is the one
place they are defined, so the build and the load cannot drift onto different
schemas, and each task passes them down as `--conf`:

| config | default | used by |
| --- | --- | --- |
| `spark.cti.source_schema` | `cti` | run.py |
| `spark.cti.target_schema` | `gold` | both |
| `spark.cti.sql_dir` | *absolute path to* `sql/` | both |
| `spark.cti.pg.schema` | `public` | load_postgres.py |
| `spark.cti.pg.url` | from the connection | load_postgres.py |
| `spark.cti.pg.user` | from the connection | load_postgres.py |
| `spark.cti.pg.password` | from the connection | load_postgres.py |

Neither Spark script reads the environment. Each falls back to the defaults
above, which is what keeps a bare `spark-submit run.py` working outside Airflow.

Postgres credentials come from an **Airflow connection** (`cti_postgres` by
default) as Jinja, so nothing is resolved while the DAG is parsed:

```python
"spark.cti.pg.password": "{{ conn.cti_postgres.password }}"
```

Naming it `...password` is deliberate — Spark's `spark.redaction.regex` matches
`secret|password|token` by default and redacts it from the UI and the event log.
It is still visible in the driver's process arguments on that host, so if that
matters, put it on the worker as a secret and read it there instead.

The two settings Airflow needs while *parsing* the DAG — where the repo is and
which Spark connection to use — cannot come from Spark. Those are Airflow
Variables (`cti_project_home`, `cti_spark_conn_id`, `cti_postgres_conn_id`,
`cti_source_schema`, `cti_target_schema`, `cti_postgres_schema`), each falling
back to a sensible default, so the DAGs work with no Variables set at all.

Templating `conf` needs `apache-airflow-providers-apache-spark` 4.x or later. On
an older provider, build the dict with `BaseHook.get_connection(...)` instead and
accept that the password is read at parse time.

## Loading into Postgres

```bash
spark-submit --packages org.postgresql:postgresql:42.7.3 load_postgres.py
spark-submit --packages org.postgresql:postgresql:42.7.3 load_postgres.py dim_country
```

| | how | why |
| --- | --- | --- |
| `dim_*` | `INSERT ... ON CONFLICT (id) DO UPDATE` | a row that leaves the lakehouse keeps its place, so anything already pointing at that id still resolves |
| `bridge_*`, `fact_report` | `TRUNCATE` + `INSERT` | derived and disposable, so a clean replacement each run |

Both go through a `<table>_stage` table: Spark writes that, then Postgres moves
it into place **in one transaction**. Two reasons for the extra hop:

- Writing straight onto the target with `mode="overwrite"` **drops** it, taking
  the indexes, constraints and grants with it.
- `TRUNCATE` and `INSERT` commit together, so readers see the old rows right up
  until the new ones are all there — never a half-loaded table.

The target table and its primary key are created from the staged table on first
run, so there is no DDL to maintain by hand. If a statement fails the whole
transaction rolls back and the task fails.

`stg_report`, `stg_entity` and `dim_key` are warehouse internals and are not
shipped. Worth considering: adding `dim_key` to the load would give you an
off-lakehouse copy of the one table you cannot rebuild.

## Postgres schema — Django

[django_warehouse/](django_warehouse) owns the Postgres DDL. `load_postgres.py`
only moves data: its `CREATE TABLE IF NOT EXISTS` becomes a no-op once these
migrations have run, so the tables keep the column types, indexes and
constraints declared in [models.py](django_warehouse/warehouse/models.py)
instead of whatever Spark's JDBC writer would have inferred.

```bash
cd django_warehouse
python manage.py migrate            # what the DAG's django_migrate task runs
```

One `models.py` holds the whole schema — 17 models in four kinds:

| kind | count | notes |
| --- | --- | --- |
| dimensions | 8 | `id` is a plain `BigIntegerField`, **not** an auto field — the value is minted in `gold.dim_key` and has to survive the trip |
| bridges | 3 | natural key is (group key, member), so they get a surrogate auto id plus a `UniqueConstraint` on the pair |
| fact | 1 | `report_id` is the key; the five dimension links are real `ForeignKey`s with `db_column` spelled out so Django does not append a second `_id` |
| views | 5 | `managed = False` — Django records them but emits no DDL |

`gold.dim_key` is deliberately **not** modelled: it is lakehouse-internal, is
never shipped to Postgres, and its natural key is the composite
`(dimension, natural_key)`, which Django could not express as a primary key
before 5.2.

The semantic views are created by
[0002_semantic_views.py](django_warehouse/warehouse/migrations/0002_semantic_views.py),
which reads the same `sql/semantic/*.sql` files Spark uses, so both engines
expose the same definitions and there is one place to change one. It drops in
reverse dependency order before creating, because `CREATE OR REPLACE VIEW` in
Postgres cannot change a view's column list.

Needs `psycopg` wherever the migration runs, including the Airflow worker:

```bash
pip install "psycopg[binary]"
```

Point it at the database with the usual `PGHOST` / `PGPORT` / `PGDATABASE` /
`PGUSER` / `PGPASSWORD`, plus `PGSCHEMA` (default `public`) — keep that in step
with `spark.cti.pg.schema`, which is where `load_postgres.py` writes. If the
repo is not next to `django_warehouse/`, set `CTI_SQL_DIR` so the view migration
can find `sql/semantic/`.


## The semantic layer

[sql/semantic/](sql/semantic) is what people actually query. Nobody outside the
warehouse should have to know an id or write a bridge join.

| view | grain |
| --- | --- |
| `vw_report` | one row per report, every single-valued dimension resolved to its name |
| `vw_report_country` | one row per report per country |
| `vw_report_entity` | one row per report per entity, with sector, category, cti_id |
| `vw_report_group` | one row per report per threat group |
| `vw_entity_coverage` | one row per metric: how far the CTI register covers what reports mention |

They are views, not tables — no storage, always current, rebuilt in a second.
`vw_report` is the spine and the fan-out views build on it, which is why the DAG
pins it to its own stage.

The fan-out views are one row per **mention**, so `COUNT(*)` over them counts
mentions, not reports. Sum `weight_factor` to count reports without double
counting — a report spread over three countries contributes 1/3 to each, and
they add back to 1:

```sql
SELECT country_name, sum(weight_factor) AS reports
FROM gold.vw_report_country
GROUP BY country_name
ORDER BY reports DESC;
```

`vw_entity_coverage` recomputes the integration breakdown that used to be pasted
as an email into the bottom of the dbt `fact_report.sql`, so it moves when the
data moves.


## The model

`fact_report` is one row per report. Single-valued attributes carry a dimension
id. Country, entity and related groups are multi-valued, so they carry a **group
key** that joins to a bridge:

```
fact_report.country_group_key -> bridge_country -> dim_country
fact_report.entity_group_key  -> bridge_entity  -> dim_entity
fact_report.group_group_key   -> bridge_group   -> dim_group
```

The group key is an MD5 of the report's members after trim/upper/dedupe/sort, so
two reports naming the same countries in any order share one group and the
bridge holds one row per distinct *set* rather than per report.
[`stg_report`](sql/staging/stg_report.sql) builds those member sets once and both
the fact and the bridges read them, so a key and its members cannot drift apart.

Multiply a measure by `weight_factor` to split a report across its members and
keep totals additive:

```sql
SELECT c.country_name, sum(b.weight_factor) AS reports
FROM gold.fact_report f
JOIN gold.bridge_country b ON f.country_group_key = b.country_group_key
JOIN gold.dim_country   c ON b.country_id = c.id
GROUP BY c.country_name;
```

Join without it for membership questions ("which reports mention Saudi Arabia").

Every dimension has an `id = -1` / 'Unknown' row, and a report with no values
hashes the sentinel member `UNKNOWN`, which resolves to it. Nothing drops out of
the fact and no foreign key is NULL.

## Known edges

- Entity members match in preference order — cti_id, prm_id, Arabic label,
  English label. `entities_rasd_id` has no counterpart in `cti.entities`, so
  those members land on `-1` and stay countable through `is_unknown_member`
  rather than disappearing. That is the "RASD id on the report but no CTI id"
  cohort.
- Two spellings of one value collapse to a single key, since `dim_key` matches
  on `upper(natural_key)`. The displayed `label` is the first one alphabetically,
  chosen with `min()` so it does not change between runs.
- A label-only entity has nothing but its name to identify it, so renaming one
  does mint a new key — the source carries no identifier tying the old name to
  the new one. Registered entities are keyed on `cti_id` and are unaffected.
- The append step reads `dim_key` while inserting into it. That is fine under
  Delta's snapshot isolation, but two builds must not run against the same
  schema concurrently, or both could mint the same id.
- `dim_country` and `dim_group` store names as written and are matched
  case-insensitively by the bridges; the dbt `dim_country` did not trim its
  tokens, which is why members could not be resolved back to an id.

## Differences from the dbt models

The dbt versions of the fact and `dim_entity` do not currently run. Fixed here:
broken `dim_cti_rasd_*` refs, `raw_data` columns that were never selected, a
trailing comma before `FROM`, `UNION ALL` branches of differing arity, an empty
`safe_cast_date` macro, and a Spark `split()` fed an unescaped `|` delimiter
(it takes a regex, so entity names shattered into characters). `dim_group` and
the three bridge models are new — they were empty files.
