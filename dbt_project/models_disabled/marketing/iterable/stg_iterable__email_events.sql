{{ config(
    materialized='incremental',
    unique_key='email_event_id',
    on_schema_change='append_new_columns'
) }}

-- Staging model for Iterable email marketing events

select
    -- Event identifiers
    {{ dbt_utils.generate_surrogate_key(['message_id', 'email', 'event_name', 'created_at']) }} as email_event_id,
    message_id::varchar as iterable_message_id,
    campaign_id::varchar as iterable_campaign_id,
    template_id::varchar as iterable_template_id,
    
    -- Recipient information
    email,
    user_id::varchar as user_id,
    
    -- Event details
    event_name,
    case 
        when event_name in ('emailSend', 'emailSendSkip') then 'send'
        when event_name in ('emailOpen', 'emailClick') then 'engagement'
        when event_name in ('emailBounce', 'emailComplaint', 'emailUnSubscribe') then 'negative'
        when event_name in ('emailSubscribe', 'emailResubscribe') then 'positive'
        else 'other'
    end as event_category,
    
    -- Campaign information
    campaign_name,
    campaign_type,
    subject_line,
    from_email,
    from_name,
    
    -- Event timing
    created_at::timestamp as event_timestamp,
    date(created_at) as event_date,
    
    -- Event context
    content_url,
    link_url,
    bounce_reason,
    unsub_source,
    
    -- Device and location (if available)
    user_agent,
    ip_address,
    city,
    region,
    country_code,
    
    -- Custom fields
    custom_fields,
    
    -- Metadata
    current_timestamp as _stg_loaded_at
    
from {{ source('iterable', 'email_events') }}

{% if is_incremental() %}
    where created_at > (select max(event_timestamp) from {{ this }})
{% endif %}
