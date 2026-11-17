with source as (

    select * from {{ source('raw', 'raw_claims') }}

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by claim_id
            order by _source_file
        ) as copy_number
    from source

)

select
    claim_id,
    member_id,
    try_to_date(service_date) as service_date,
    service_type,
    try_cast(amount_usd as number(12, 2)) as amount_usd,
    claim_status,
    try_to_timestamp(submitted_at) as submitted_at,
    _source_file
from deduplicated
where copy_number = 1
