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
        
        -- Extract contact and owner IDs from associations (handle JSON safely)
        case
            when associations is not null and associations::text != 'null' then 
                associations->>'contactIds'
            else null
        end as contact_ids,
        
        case
            when associations is not null and associations::text != 'null' then 
                associations->>'companyIds'
            else null
        end as company_ids,
        
        case
            when associations is not null and associations::text != 'null' then 
                associations->>'dealIds'
            else null
        end as deal_ids,
        
        -- Extract owner from properties (handle JSON safely)
        case
            when properties is not null and properties::text != 'null' then 
                properties->>'hubspot_owner_id'
            else null
        end as owner_id,
        
        -- Ticket Details from columns
        coalesce(subject, '') as subject,
        coalesce(content, '') as content,
        coalesce(hs_pipeline, 'default') as pipeline,
        coalesce(hs_pipeline_stage, 'new') as status,
        coalesce(hs_ticket_priority, 'low') as priority,
        coalesce(archived, false) as archived,
        
        -- Additional fields from properties (handle JSON safely)
        case
            when properties is not null and properties::text != 'null' then 
                properties->>'hs_ticket_category'
            else null
        end as ticket_category,
        
        case
            when properties is not null and properties::text != 'null' then 
                properties->>'source_type'
            else null
        end as source_type,
        
        -- Dates
        coalesce(createdate, created_at) as created_at,
        coalesce(hs_lastmodifieddate, createdate, created_at) as updated_at,
        
        -- Check if ticket is closed (handle JSON and date conversion safely)
        case
            when properties is not null 
                and properties::text != 'null' 
                and properties->>'closed_date' is not null 
                and properties->>'closed_date' != '' 
                and properties->>'closed_date' ~ '^\d+$' then
                to_timestamp((properties->>'closed_date')::bigint / 1000)
            else null
        end as closed_at,
        
        -- Status Categorization
        case
            when lower(coalesce(hs_pipeline_stage, '')) in ('new', 'waiting_on_contact') then 'Open'
            when lower(coalesce(hs_pipeline_stage, '')) in ('in_progress', 'waiting_on_us') then 'In Progress'
            when lower(coalesce(hs_pipeline_stage, '')) in ('closed', 'resolved') then 'Closed'
            else 'Other'
        end as status_category,
        
        -- Priority Scoring
        case
            when lower(coalesce(hs_ticket_priority, '')) = 'high' then 3
            when lower(coalesce(hs_ticket_priority, '')) = 'medium' then 2
            when lower(coalesce(hs_ticket_priority, '')) = 'low' then 1
            else 0
        end as priority_score,
        
        -- Resolution Metrics (handle date calculations safely)
        case
            when properties is not null 
                and properties::text != 'null' 
                and properties->>'closed_date' is not null 
                and properties->>'closed_date' != '' 
                and properties->>'closed_date' ~ '^\d+$'
                and createdate is not null then
                extract(epoch from (
                    to_timestamp((properties->>'closed_date')::bigint / 1000) - createdate
                )) / 3600
            else null
        end as resolution_time_hours,
        
        case
            when properties is not null 
                and properties::text != 'null' 
                and properties->>'closed_date' is not null 
                and properties->>'closed_date' != '' 
                and properties->>'closed_date' ~ '^\d+$'
                and createdate is not null then
                extract(day from (
                    to_timestamp((properties->>'closed_date')::bigint / 1000) - createdate
                ))
            else null
        end as resolution_time_days,
        
        -- Age Calculation (for open tickets)
        case
            when (properties is null or properties::text = 'null' or properties->>'closed_date' is null)
                and createdate is not null then 
                extract(day from (current_timestamp - createdate))
            else null
        end as ticket_age_days,
        
        -- SLA Categories (simplified, handle nulls)
        case
            when lower(coalesce(hs_ticket_priority, '')) = 'high' 
                and (properties is null or properties::text = 'null' or properties->>'closed_date' is null)
                and createdate is not null
                and extract(hour from (current_timestamp - createdate)) > 4 then 'SLA Breach'
            when lower(coalesce(hs_ticket_priority, '')) = 'medium' 
                and (properties is null or properties::text = 'null' or properties->>'closed_date' is null)
                and createdate is not null
                and extract(hour from (current_timestamp - createdate)) > 24 then 'SLA Breach'
            when lower(coalesce(hs_ticket_priority, '')) = 'low' 
                and (properties is null or properties::text = 'null' or properties->>'closed_date' is null)
                and createdate is not null
                and extract(hour from (current_timestamp - createdate)) > 72 then 'SLA Breach'
            else 'Within SLA'
        end as sla_status,
        
        -- Subject Analysis
        case
            when lower(coalesce(subject, '')) like '%bug%' or lower(coalesce(subject, '')) like '%error%' then 'Bug'
            when lower(coalesce(subject, '')) like '%feature%' or lower(coalesce(subject, '')) like '%request%' then 'Feature Request'
            when lower(coalesce(subject, '')) like '%billing%' or lower(coalesce(subject, '')) like '%payment%' then 'Billing'
            when lower(coalesce(subject, '')) like '%cancel%' or lower(coalesce(subject, '')) like '%refund%' then 'Cancellation'
            else 'General Support'
        end as ticket_category_derived,
        
        -- Data Quality
        case
            when id is null then 'Missing Ticket ID'
            when subject is null or subject = '' then 'Missing Subject'
            when hs_pipeline_stage is null then 'Missing Status'
            when createdate is null and created_at is null then 'Missing Created Date'
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