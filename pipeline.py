"""
pipeline.py - orchestrates the whole pipeline with Prefect.

Order: load raw files -> build dbt models -> run dbt tests.
Run it:   python pipeline.py
"""
import subprocess
import sys

from dotenv import load_dotenv
from prefect import flow, task
from prefect.logging import get_run_logger

# Load .env into environment variables so subprocesses (load_raw.py, dbt) inherit them
load_dotenv()


def run_cmd(cmd, cwd=None):
    """Run a shell command; raise an error if it fails so Prefect marks the task failed."""
    logger = get_run_logger()
    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        logger.info(result.stdout[-2000:])
    if result.returncode != 0:
        logger.error(result.stderr[-2000:] or result.stdout[-2000:])
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")


@task(retries=2, retry_delay_seconds=10)
def load_raw_files():
    # Safe to retry: the loader skips files that are already loaded (idempotent)
    run_cmd([sys.executable, "load_raw.py"])


@task
def dbt_run():
    run_cmd(["dbt", "run", "--profiles-dir", "."], cwd="carrot_dbt")


@task
def dbt_test():
    run_cmd(["dbt", "test", "--profiles-dir", "."], cwd="carrot_dbt")


def alert_on_failure(flow, flow_run, state):
    # In production this would post to Slack or PagerDuty
    print(f"\n*** ALERT: flow '{flow.name}' (run '{flow_run.name}') FAILED: {state.message}\n")


@flow(name="carrot-daily-pipeline", on_failure=[alert_on_failure])
def daily_pipeline():
    load_raw_files()
    dbt_run()
    dbt_test()


if __name__ == "__main__":
    daily_pipeline()
