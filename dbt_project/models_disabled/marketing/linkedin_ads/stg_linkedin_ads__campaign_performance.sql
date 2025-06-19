{{ config(
    materialized='incremental',
    unique_key=['campaign_id', 'date'],
    on_schema_change='append_new_columns'
) }}

-- Staging model for LinkedIn Ads campaign performance

select
    -- Campaign identifiers
    campaign_id::varchar as linkedin_campaign_id,
    campaign_name,
    status as campaign_status,
    campaign_type,
    objective_type as campaign_objective,
    
    -- Date and performance metrics
    date_range:start::date as performance_date,
    impressions,
    clicks,
    cost_in_usd::decimal as cost_usd,
    
    -- LinkedIn-specific metrics
    follows,
    company_page_clicks,
    leads,
    lead_generation_mail_contact_info,
    lead_generation_mail_interest_clicked,
    
    -- Video metrics
    video_views,
    video_completions,
    video_first_quartile_completions,
    
    -- Engagement metrics
    likes,
    comments,
    shares,
    other_engagements,
    
    -- Conversion tracking
    conversion_value_in_usd::decimal as conversion_value_usd,
    coalesce(external_website_conversions, 0) as conversions,
    
    -- Calculated metrics
    case 
        when impressions > 0 then clicks / impressions::decimal
        else 0
    end as click_through_rate,
    
    case 
        when clicks > 0 then cost_in_usd / clicks
        else 0
    end as cost_per_click,
    
    case 
        when leads > 0 then cost_in_usd / leads
        else 0
    end as cost_per_lead,
    
    -- Channel standardization
    'linkedin_ads' as marketing_channel,
    case 
        when objective_type = 'LEAD_GENERATION' then 'paid_social_leads'
        when objective_type = 'WEBSITE_CONVERSIONS' then 'paid_social_conversion'
        when objective_type = 'BRAND_AWARENESS' then 'paid_social_awareness'
        when objective_type = 'WEBSITE_VISITS' then 'paid_social_traffic'
        else 'paid_social_other'
    end as channel_type,
    
    -- Account information
    account_id as linkedin_account_id,
    
    -- Metadata
    current_timestamp as _stg_loaded_at
    
from {{ source('linkedin_ads', 'campaign_analytics') }}

{% if is_incremental() %}
    where date_range:start::date >= (select max(performance_date) from {{ this }})
{% endif %}
