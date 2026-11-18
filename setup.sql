-- Run once in Snowflake before loading data
CREATE DATABASE IF NOT EXISTS CARROT_PRACTICE;
CREATE SCHEMA IF NOT EXISTS CARROT_PRACTICE.RAW;
USE SCHEMA CARROT_PRACTICE.RAW;

CREATE TABLE IF NOT EXISTS RAW_ELIGIBILITY (
    member_id VARCHAR, employer_id VARCHAR, first_name VARCHAR, last_name VARCHAR,
    date_of_birth VARCHAR, email VARCHAR, country VARCHAR, coverage_start VARCHAR,
    coverage_end VARCHAR, status VARCHAR,
    _source_file VARCHAR,
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS RAW_CLAIMS (
    claim_id VARCHAR, member_id VARCHAR, service_date VARCHAR, service_type VARCHAR,
    amount_usd VARCHAR, claim_status VARCHAR, submitted_at VARCHAR,
    _source_file VARCHAR,
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
