{{ config(severity='warn') }}

select claim_id, service_date, submitted_at
from {{ ref('stg_claims') }}
where service_date > cast(submitted_at as date)
