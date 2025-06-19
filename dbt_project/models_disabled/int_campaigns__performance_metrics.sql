{{
    config(
        materialized = 'table'
    )
}}

with google_ads as (
    select * from {{ ref('stg_google_ads__campaign_performance') }}
),

meta_ads as (
    select * from {{ ref('stg_meta_ads__campaign_performance') }}
),

hubspot_campaigns as (
    select * from {{ ref('stg_hubspot__email_campaigns') }}
),

hubspot_events as (
    select * from {{ ref('stg_hubspot__email_events') }}
),

-- Normalize campaign data from different sources
normalized_campaigns as (
    -- Google Ads campaigns
    select
        'google_ads' as campaign_source,
        campaign_id,
        campaign_name,
        campaign_type,
        campaign_status,
        date as campaign_date,
        impressions,
        clicks,
        cost as spend,
        conversions,
        conversion_value as revenue,
        null as emails_sent,
        null as emails_delivered,
        null as emails_opened,
        null as emails_clicked,
        null as emails_unsubscribed
    from google_ads
    
    union all
    
    -- Meta Ads campaigns
    select
        'meta_ads' as campaign_source,
        campaign_id,
        campaign_name,
        objective as campaign_type,
        status as campaign_status,
        date as campaign_date,
        impressions,
        clicks,
        spend,
        conversions,
        conversion_value as revenue,
        null as emails_sent,
        null as emails_delivered,
        null as emails_opened,
        null as emails_clicked,
        null as emails_unsubscribed
    from meta_ads
    
    union all
    
    -- HubSpot email campaigns
    select
        'hubspot_email' as campaign_source,
        campaign_id::varchar as campaign_id,
        campaign_name,
        campaign_type,
        campaign_status,
        date(sent_at) as campaign_date,
        null as impressions,
        num_clicked as clicks,
        null as spend,
        null as conversions,
        null as revenue,
        num_sent as emails_sent,
        num_delivered as emails_delivered,
        num_opened as emails_opened,
        num_clicked as emails_clicked,
        num_unsubscribed as emails_unsubscribed
    from hubspot_campaigns
    where sent_at is not null
),

-- Aggregate campaign metrics
campaign_metrics as (
    select
        campaign_source,
        campaign_id,
        campaign_name,
        campaign_type,
        campaign_status,
        min(campaign_date) as campaign_start_date,
        max(campaign_date) as campaign_end_date,
        count(distinct campaign_date) as days_active,
        
        -- Paid media metrics
        sum(impressions) as total_impressions,
        sum(clicks) as total_clicks,
        sum(spend) as total_spend,
        sum(conversions) as total_conversions,
        sum(revenue) as total_revenue,
        
        -- Email metrics
        sum(emails_sent) as total_emails_sent,
        sum(emails_delivered) as total_emails_delivered,
        sum(emails_opened) as total_emails_opened,
        sum(emails_clicked) as total_emails_clicked,
        sum(emails_unsubscribed) as total_emails_unsubscribed,
        
        -- Calculated metrics
        case when sum(impressions) > 0 then sum(clicks)::float / sum(impressions) else 0 end as click_through_rate,
        case when sum(clicks) > 0 then sum(conversions)::float / sum(clicks) else 0 end as conversion_rate,
        case when sum(spend) > 0 then sum(conversions)::float / sum(spend) else 0 end as conversions_per_dollar,
        case when sum(spend) > 0 then sum(revenue)::float / sum(spend) else 0 end as return_on_ad_spend,
        case when sum(conversions) > 0 then sum(spend)::float / sum(conversions) else 0 end as cost_per_conversion,
        case when sum(clicks) > 0 then sum(spend)::float / sum(clicks) else 0 end as cost_per_click,
        
        -- Email-specific rates
        case when sum(emails_sent) > 0 then sum(emails_delivered)::float / sum(emails_sent) else 0 end as email_delivery_rate,
        case when sum(emails_delivered) > 0 then sum(emails_opened)::float / sum(emails_delivered) else 0 end as email_open_rate,
        case when sum(emails_opened) > 0 then sum(emails_clicked)::float / sum(emails_opened) else 0 end as email_click_rate,
        case when sum(emails_delivered) > 0 then sum(emails_unsubscribed)::float / sum(emails_delivered) else 0 end as email_unsubscribe_rate
        
    from normalized_campaigns
    group by 1, 2, 3, 4, 5
),

-- Add performance scoring
campaign_performance as (
    select
        *,
        
        -- Performance score (0-100) based on channel
        case
            when campaign_source in ('google_ads', 'meta_ads') then
                round(
                    (
                        -- ROI component (40%)
                        case 
                            when return_on_ad_spend >= 4 then 40
                            when return_on_ad_spend >= 2 then 30
                            when return_on_ad_spend >= 1 then 20
                            else return_on_ad_spend * 20
                        end +
                        -- Conversion rate component (30%)
                        case
                            when conversion_rate >= 0.05 then 30
                            else conversion_rate * 600
                        end +
                        -- Click-through rate component (30%)
                        case
                            when click_through_rate >= 0.02 then 30
                            else click_through_rate * 1500
                        end
                    ), 2
                )
            when campaign_source = 'hubspot_email' then
                round(
                    (
                        -- Open rate component (40%)
                        case
                            when email_open_rate >= 0.25 then 40
                            else email_open_rate * 160
                        end +
                        -- Click rate component (40%)
                        case
                            when email_click_rate >= 0.1 then 40
                            else email_click_rate * 400
                        end +
                        -- Unsubscribe rate component (20%, inverse)
                        case
                            when email_unsubscribe_rate <= 0.002 then 20
                            when email_unsubscribe_rate >= 0.01 then 0
                            else (1 - (email_unsubscribe_rate / 0.01)) * 20
                        end
                    ), 2
                )
            else 0
        end as performance_score,
        
        -- Campaign effectiveness tier
        case
            when campaign_source in ('google_ads', 'meta_ads') then
                case
                    when return_on_ad_spend >= 4 and conversion_rate >= 0.05 then 'High Performer'
                    when return_on_ad_spend >= 2 and conversion_rate >= 0.02 then 'Good Performer'
                    when return_on_ad_spend >= 1 then 'Average Performer'
                    else 'Under Performer'
                end
            when campaign_source = 'hubspot_email' then
                case
                    when email_open_rate >= 0.25 and email_click_rate >= 0.1 then 'High Performer'
                    when email_open_rate >= 0.15 and email_click_rate >= 0.05 then 'Good Performer'
                    when email_open_rate >= 0.1 then 'Average Performer'
                    else 'Under Performer'
                end
            else 'Unknown'
        end as performance_tier,
        
        -- Current status
        case
            when campaign_status in ('ENABLED', 'ACTIVE', 'published') then 'Active'
            when campaign_status in ('PAUSED', 'scheduled') then 'Paused'
            when campaign_status in ('REMOVED', 'ENDED', 'archived') then 'Ended'
            else 'Unknown'
        end as normalized_status,
        
        current_timestamp() as _synced_at
        
    from campaign_metrics
)

select * from campaign_performance