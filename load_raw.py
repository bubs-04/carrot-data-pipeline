import os
import warnings
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

warnings.filterwarnings("ignore", message="enable_server_session_keep_alive_auto_detection")
load_dotenv()

LANDING = Path("landing")

# table name -> (folder holding its files, column names in file order)
TABLES = {
    "RAW_ELIGIBILITY": (
        LANDING / "eligibility",
        ["member_id", "employer_id", "first_name", "last_name", "date_of_birth",
         "email", "country", "coverage_start", "coverage_end", "status"],
    ),
    "RAW_CLAIMS": (
        LANDING / "claims",
        ["claim_id", "member_id", "service_date", "service_type",
         "amount_usd", "claim_status", "submitted_at"],
    ),
}


def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )


def already_loaded(cur, table, file_name):
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE _source_file = %s", (file_name,))
    return cur.fetchone()[0] > 0


def load_file(cur, table, columns, path):
    # 1. Upload the local file into this table's own stage
    cur.execute(
        f"PUT 'file://{path.resolve().as_posix()}' @%{table} "
        "AUTO_COMPRESS = FALSE OVERWRITE = TRUE"
    )
    # 2. Copy from the stage into the table, recording the file name
    col_list = ", ".join(columns)
    select_list = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
    cur.execute(f"""
        COPY INTO {table} ({col_list}, _source_file)
        FROM (SELECT {select_list}, '{path.name}' FROM @%{table})
        FILES = ('{path.name}')
        FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"')
    """)
    result = cur.fetchall()
    return result[0][3] if len(result[0]) > 3 else 0


def main():
    conn = get_connection()
    cur = conn.cursor()
    loaded = skipped = 0
    for table, (folder, columns) in TABLES.items():
        for path in sorted(folder.glob("*.csv")):
            if already_loaded(cur, table, path.name):
                print(f"skip    {path.name} (already loaded)")
                skipped += 1
                continue
            rows = load_file(cur, table, columns, path)
            print(f"loaded  {path.name}: {rows} rows")
            loaded += 1
    print(f"\n{loaded} files loaded, {skipped} skipped")
    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {cur.fetchone()[0]} rows")
    conn.close()


if __name__ == "__main__":
    main()
