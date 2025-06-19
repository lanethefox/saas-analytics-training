{{ config(
    materialized='incremental',
    unique_key='ticket_id',
    on_schema_change='fail',
    tags=['hubspot', 'support']
) }}

with source as (
    select * from {{ source('hubspot', 'tickets') }}
),

{% if is_incremental() %}
max_createdate as (
    select max(created_at) as max_created from {{ this }}
),

filtered_source as (
    select 
        source.*
    from source
    cross join max_createdate
    where source.createdate > max_createdate.max_created
),
{% else %}
filtered_source as (
    select * from source
),
{% endif %}

renamed as (
    select
        -- IDs
        id as ticket_id,
        
        -- Extract contact and owner IDs from associations
        associations->>'contactIds' as contact_ids,
        associations->>'companyIds' as company_ids,
        associations->>'dealIds' as deal_ids,
        
        -- Extract owner from properties
        properties->>'hubspot_owner_id' as owner_id,
        
        -- Ticket Details from columns
        subject,
        content,
        hs_pipeline as pipeline,
        hs_pipeline_stage as status,
        hs_ticket_priority as priority,
        archived,
        
        -- Additional fields from properties
        properties->>'hs_ticket_category' as ticket_category,
        properties->>'source_type' as source_type,
        
        -- Dates
        createdate as created_at,
        hs_lastmodifieddate as updated_at,
        
        -- Check if ticket is closed
        case
            when properties->>'closed_date' is not null then 
                to_timestamp((properties->>'closed_date')::bigint / 1000)
            else null
        end as closed_at,
        
        -- Status Categorization
        case
            when lower(hs_pipeline_stage) in ('new', 'waiting_on_contact') then 'Open'
            when lower(hs_pipeline_stage) in ('in_progress', 'waiting_on_us') then 'In Progress'
            when lower(hs_pipeline_stage) in ('closed', 'resolved') then 'Closed'
            else 'Other'
        end as status_category,
        
        -- Priority Scoring
        case
            when lower(hs_ticket_priority) = 'high' then 3
            when lower(hs_ticket_priority) = 'medium' then 2
            when lower(hs_ticket_priority) = 'low' then 1
            else 0
        end as priority_score,
        
        -- Resolution Metrics
        case
            when properties->>'closed_date' is not null then 
                extract(epoch from (
                    to_timestamp((properties->>'closed_date')::bigint / 1000) - createdate
                )) / 3600
            else null
        end as resolution_time_hours,
        
        case
            when properties->>'closed_date' is not null then 
                extract(day from (
                    to_timestamp((properties->>'closed_date')::bigint / 1000) - createdate
                ))
            else null
        end as resolution_time_days,
        
        -- Age Calculation (for open tickets)
        case
            when properties->>'closed_date' is null then 
                extract(day from (current_timestamp - createdate))
            else null
        end as ticket_age_days,
        
        -- SLA Categories (simplified)
        case
            when lower(hs_ticket_priority) = 'high' 
                and properties->>'closed_date' is null 
                and extract(hour from (current_timestamp - createdate)) > 4 then 'SLA Breach'
            when lower(hs_ticket_priority) = 'medium' 
                and properties->>'closed_date' is null 
                and extract(hour from (current_timestamp - createdate)) > 24 then 'SLA Breach'
            when lower(hs_ticket_priority) = 'low' 
                and properties->>'closed_date' is null 
                and extract(hour from (current_timestamp - createdate)) > 72 then 'SLA Breach'
            else 'Within SLA'
        end as sla_status,
        
        -- Subject Analysis
        case
            when lower(subject) like '%bug%' or lower(subject) like '%error%' then 'Bug'
            when lower(subject) like '%feature%' or lower(subject) like '%request%' then 'Feature Request'
            when lower(subject) like '%billing%' or lower(subject) like '%payment%' then 'Billing'
            when lower(subject) like '%cancel%' or lower(subject) like '%refund%' then 'Cancellation'
            else 'General Support'
        end as ticket_category_derived,
        
        -- Data Quality
        case
            when id is null then 'Missing Ticket ID'
            when subject is null or subject = '' then 'Missing Subject'
            when hs_pipeline_stage is null then 'Missing Status'
            when createdate is null then 'Missing Created Date'
            else 'Valid'
        end as data_quality_flag,
        
        -- Audit Fields
        current_timestamp as _dbt_inserted_at

    from filtered_source
),

final as (
    select * from renamed
)

select * from final