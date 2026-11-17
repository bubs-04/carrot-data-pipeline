with source as (

    select * from {{ source('raw', 'raw_eligibility') }}

),

with_file_date as (

    select
        *,
        try_to_date(
            regexp_substr(_source_file, '[0-9]{4}-[0-9]{2}-[0-9]{2}')
        ) as file_date
    from source

),

latest_record as (

    select
        *,
        row_number() over (
            partition by member_id
            order by file_date desc
        ) as recency_rank
    from with_file_date

)

select
    member_id,
    employer_id,
    first_name,
    last_name,
    coalesce(
        try_to_date(date_of_birth, 'YYYY-MM-DD'),
        try_to_date(date_of_birth, 'MM/DD/YYYY')
    ) as date_of_birth,
    nullif(trim(email), '') as email,
    case upper(trim(country))
        when 'US' then 'US'
        when 'USA' then 'US'
        when 'UNITED STATES' then 'US'
        when 'GB' then 'GB'
        when 'UK' then 'GB'
        when 'UNITED KINGDOM' then 'GB'
        when 'CA' then 'CA'
        when 'CANADA' then 'CA'
        when 'DE' then 'DE'
        when 'GERMANY' then 'DE'
        when 'IN' then 'IN'
        when 'INDIA' then 'IN'
    end as country_code,
    try_to_date(coverage_start) as coverage_start,
    try_to_date(coverage_end) as coverage_end,
    status,
    file_date as last_seen_file_date
from latest_record
where recency_rank = 1
