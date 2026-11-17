{{ config(severity='warn') }}

select claim_id, amount_usd
from {{ ref('stg_claims') }}
where amount_usd < 0
