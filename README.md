# Carrot-style data pipeline (practice project)

An end-to-end ELT pipeline built to learn the modern data stack hands-on:
Python, Snowflake, dbt, Prefect, and Git. **All data is synthetic.**

It simulates the files a fertility-benefits platform might receive from employers
(eligibility) and claims partners, loads them into Snowflake, cleans and tests them
with dbt, and produces a per-employer utilization table.

## Pipeline

    generate_data.py  ->  landing/*.csv  ->  load_raw.py  ->  Snowflake RAW
        ->  dbt staging (typed, de-duplicated)  ->  dbt mart (per-employer utilization)

`pipeline.py` runs load, dbt run, and dbt test in order using Prefect, with retries
and a failure alert.

## Design decisions

- **Raw layer is all text.** A bad value can never fail the load. Every row records its
  `_source_file` and `_loaded_at` for lineage and auditing.
- **The loader is idempotent.** It skips files already loaded. My first version doubled
  the data on a re-run because it compared bare file names to stage paths. I found it by
  testing a second run, inspected what was stored, fixed it, and re-verified.
- **Staging models** de-duplicate, convert types safely (`try_` functions), and standardize
  12 country spellings into 5 codes.
- **dbt tests with deliberate severity.** Duplicate or missing IDs would corrupt every
  number, so they are errors. Partner data problems (negative amounts, unknown members) are
  warnings: flag them and report back instead of blocking everyone.
- **The mart only uses trusted rows and is aggregated per employer**, with no member-level
  fields, in the spirit of multi-tenant reporting.
- **Secrets live in a git-ignored `.env`.** `profiles.yml` holds only variable names.
- **Prefect** stops the flow when loading fails, so models are never built on missing data.

## Planted data problems and how each is handled

| Problem | Count | Handling |
|---|---|---|
| Duplicate claims re-sent by partner | 12 | Staging keeps first copy (`row_number`) |
| Negative amounts | 6 | dbt test (warn), excluded from mart |
| Missing amounts | 9 | dbt test (warn), excluded from mart |
| Claims for unknown member | 10 | dbt relationships test (warn), excluded from mart |
| Service date after submission | 17 | dbt test (warn), excluded from mart |
| Country spelling variants | 12 for 5 | Standardized in staging, accepted-values test |
| Mixed date-of-birth formats | 27 | Two-format parse in staging |
| Missing emails | 33 | dbt test (warn) |

Results were checked against independent calculations from the raw files, and
row counts reconcile at each layer (3,135 raw eligibility rows -> 1,050 members;
912 raw claims -> 900 after de-duplication).

## Run it

1. Create a Snowflake trial account and run `setup.sql`.
2. Create a `.env` file with SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
   SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA.
3. Then:

        conda create -n carrot python=3.11
        conda activate carrot
        pip install dbt-snowflake prefect
        python generate_data.py
        python pipeline.py

## Not built yet (honest scope)

Real SFTP and S3 ingestion, column masking and row-level security, incremental dbt models,
CI, and Slack alerting. These are the next steps.

## How this was built

Built with AI assistance as a learning exercise. I ran every step, debugged the failures,
and checked the numbers independently, and I can explain each part.
