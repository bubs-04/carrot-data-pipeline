import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()  # reads .env into environment variables

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    schema=os.environ["SNOWFLAKE_SCHEMA"],
)
print(conn.cursor().execute("SELECT CURRENT_USER(), CURRENT_DATABASE()").fetchone())
conn.close()
