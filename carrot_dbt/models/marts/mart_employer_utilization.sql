with valid_claims as (

    select *
    from {{ ref('stg_claims') }}
    where amount_usd > 0
      and service_date <= cast(submitted_at as date)

),

members as (

    select member_id, employer_id, status
    from {{ ref('stg_eligibility') }}

),

employer_sizes as (

    select
        employer_id,
        count_if(status = 'active') as active_members
    from members
    group by employer_id

),

employer_claims as (

    select
        m.employer_id,
        count(*) as claim_count,
        count(distinct c.member_id) as members_with_claims,
        sum(c.amount_usd) as total_claimed_usd,
        sum(case when c.claim_status = 'approved' then c.amount_usd else 0 end) as approved_usd
    from valid_claims as c
    inner join members as m
        on c.member_id = m.member_id
    group by m.employer_id

)

select
    s.employer_id,
    s.active_members,
    c.members_with_claims,
    round(100.0 * c.members_with_claims / s.active_members, 1) as utilization_pct,
    c.claim_count,
    c.total_claimed_usd,
    c.approved_usd
from employer_sizes as s
left join employer_claims as c
    on s.employer_id = c.employer_id
order by s.employer_id
